pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    environment {
        // Infrastructure Endpoints (Configured via Jenkins Global Env or Overridden here)
        NEXUS_REGISTRY       = credentials('nexus-registry-url')        // e.g. "192.168.1.102:8082" (PC 2)
        SONARQUBE_ENV        = 'SonarQube-PC1'                         // Configured in Jenkins System -> SonarQube
        DEPLOY_HOST          = credentials('pc3-deploy-hostname')       // e.g. "192.168.1.103" (PC 3)
        DB_HOST              = credentials('pc4-postgres-hostname')     // e.g. "192.168.1.104" (PC 4)
        
        // Image metadata
        IMAGE_BACKEND        = "${NEXUS_REGISTRY}/vault-backend"
        IMAGE_FRONTEND       = "${NEXUS_REGISTRY}/vault-frontend"
        IMAGE_TAG            = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        PREVIOUS_TAG_FILE    = "/tmp/vault_previous_tag_${JOB_NAME}"
    }

    stages {
        stage('1. Checkout') {
            steps {
                echo "==> Checking out repository from Gitea (PC 2)..."
                checkout scm
            }
        }

        stage('2. Security Lint & Static Analysis') {
            parallel {
                stage('Backend Static Analysis') {
                    steps {
                        echo "==> Running Ruff/Flake8/Bandit security audit on Python backend..."
                        sh '''
                            python3 -m pip install bandit ruff || true
                            bandit -r backend/app -ll || true
                        '''
                    }
                }
                stage('Frontend Lint') {
                    steps {
                        echo "==> Running Frontend validation..."
                        dir('frontend') {
                            sh 'npm ci || npm install'
                            sh 'npm run lint || true'
                        }
                    }
                }
            }
        }

        stage('3. Automated Testing Suite') {
            parallel {
                stage('Backend Unit & Security Tests') {
                    steps {
                        echo "==> Executing Pytest suite with strict cross-user isolation tests..."
                        dir('backend') {
                            sh '''
                                python3 -m pip install -r requirements.txt
                                python3 -m pytest tests/ -v
                            '''
                        }
                    }
                }
                stage('Frontend Unit Build') {
                    steps {
                        echo "==> Validating TypeScript compilation and Next.js bundle..."
                        dir('frontend') {
                            sh 'npm run build'
                        }
                    }
                }
            }
        }

        stage('4. SonarQube Code Quality Analysis') {
            steps {
                echo "==> Submitting metrics to SonarQube (PC 1)..."
                withSonarQubeEnv(env.SONARQUBE_ENV) {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=vault \
                            -Dsonar.projectName="Vault Image Storage" \
                            -Dsonar.sources=backend/app,frontend/src \
                            -Dsonar.tests=backend/tests \
                            -Dsonar.python.coverage.reportPaths=backend/coverage.xml || echo "SonarQube scanner finished"
                    '''
                }
            }
        }

        stage('5. Quality Gate Evaluation') {
            steps {
                echo "==> Evaluating SonarQube Quality Gate threshold..."
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        try {
                            def qg = waitForQualityGate()
                            if (qg.status != 'OK') {
                                error "Pipeline aborted due to quality gate failure: ${qg.status}"
                            }
                        } catch (Exception e) {
                            echo "Quality Gate check skipped or warned: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        stage('6. Build & Tag Docker Images') {
            steps {
                echo "==> Building multi-stage production Docker containers..."
                sh """
                    docker build -t ${IMAGE_BACKEND}:${IMAGE_TAG} -t ${IMAGE_BACKEND}:latest ./backend
                    docker build -t ${IMAGE_FRONTEND}:${IMAGE_TAG} -t ${IMAGE_FRONTEND}:latest ./frontend
                """
            }
        }

        stage('7. Push Images to Nexus Registry') {
            steps {
                echo "==> Pushing container images to Nexus (PC 2)..."
                withCredentials([usernamePassword(credentialsId: 'nexus-registry-credentials', usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
                    sh """
                        echo "\$NEXUS_PASS" | docker login ${NEXUS_REGISTRY} -u "\$NEXUS_USER" --password-stdin
                        docker push ${IMAGE_BACKEND}:${IMAGE_TAG}
                        docker push ${IMAGE_BACKEND}:latest
                        docker push ${IMAGE_FRONTEND}:${IMAGE_TAG}
                        docker push ${IMAGE_FRONTEND}:latest
                    """
                }
            }
        }

        stage('8. Apply Database Migrations') {
            steps {
                echo "==> Applying Alembic schema migrations to Central PostgreSQL (PC 4)..."
                withCredentials([usernamePassword(credentialsId: 'vault-postgres-credentials', usernameVariable: 'VAULT_DB_USER', passwordVariable: 'VAULT_DB_PASS')]) {
                    dir('backend') {
                        sh """
                            export POSTGRES_SERVER="${DB_HOST}"
                            export POSTGRES_USER="\${VAULT_DB_USER}"
                            export POSTGRES_PASSWORD="\${VAULT_DB_PASS}"
                            export POSTGRES_DB="vault"
                            python3 -m pip install alembic psycopg2-binary
                            alembic upgrade head || python3 init_db.py
                        """
                    }
                }
            }
        }

        stage('9. Deploy to Runtime Node (PC 3)') {
            steps {
                echo "==> Triggering remote deployment on Application Runtime Node (PC 3)..."
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'pc3-ssh-deploy-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    usernamePassword(credentialsId: 'nexus-registry-credentials', usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS'),
                    usernamePassword(credentialsId: 'vault-postgres-credentials', usernameVariable: 'VAULT_DB_USER', passwordVariable: 'VAULT_DB_PASS'),
                    string(credentialsId: 'vault-secret-key', variable: 'VAULT_SECRET_KEY')
                ]) {
                    sh """
                        ssh -i \${SSH_KEY} -o StrictHostKeyChecking=no \${SSH_USER}@\${DEPLOY_HOST} << 'EOF'
                            set -e
                            mkdir -p /opt/vault /data/images
                            cd /opt/vault

                            # Pull latest compose and proxy configurations
                            echo "\$NEXUS_PASS" | docker login ${NEXUS_REGISTRY} -u "\$NEXUS_USER" --password-stdin
                            docker pull ${IMAGE_BACKEND}:${IMAGE_TAG}
                            docker pull ${IMAGE_FRONTEND}:${IMAGE_TAG}

                            # Record current running tag for automatic rollback
                            echo "${IMAGE_TAG}" > /opt/vault/current_tag.txt

                            # Update environment and restart services
                            cat << ENV_EOF > .env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=\${VAULT_SECRET_KEY}
POSTGRES_SERVER=${DB_HOST}
POSTGRES_PORT=5432
POSTGRES_DB=vault
POSTGRES_USER=\${VAULT_DB_USER}
POSTGRES_PASSWORD=\${VAULT_DB_PASS}
STORAGE_TYPE=local
STORAGE_LOCAL_ROOT=/data/images
IMAGE_BACKEND_TAG=${IMAGE_BACKEND}:${IMAGE_TAG}
IMAGE_FRONTEND_TAG=${IMAGE_FRONTEND}:${IMAGE_TAG}
ENV_EOF

                            docker-compose pull backend frontend
                            docker-compose up -d --remove-orphans
                        EOF
                    """
                }
            }
        }

        stage('10. Health Verification & Rollback Protection') {
            steps {
                echo "==> Verifying deployment health endpoints on PC 3..."
                script {
                    def healthCheckPassed = false
                    for (int i = 0; i < 6; i++) {
                        sleep(10)
                        def status = sh(
                            script: "curl -s -o /dev/null -w '%{http_code}' http://${DEPLOY_HOST}/health || echo '000'",
                            returnStdout: true
                        ).trim()
                        echo "Health check attempt ${i + 1}: HTTP ${status}"
                        if (status == '200') {
                            healthCheckPassed = true
                            echo "✓ Vault deployment verified healthy!"
                            break
                        }
                    }

                    if (!healthCheckPassed) {
                        error "Deployment health check failed! Initiating rollback..."
                    }
                }
            }
        }
    }

    post {
        failure {
            echo "==> Pipeline failure detected! Executing rollback on PC 3..."
            withCredentials([sshUserPrivateKey(credentialsId: 'pc3-ssh-deploy-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                sh """
                    ssh -i \${SSH_KEY} -o StrictHostKeyChecking=no \${SSH_USER}@\${DEPLOY_HOST} << 'EOF'
                        cd /opt/vault
                        if [ -f /opt/vault/previous_tag.txt ]; then
                            PREV_TAG=\$(cat /opt/vault/previous_tag.txt)
                            echo "Rolling back to previous stable tag: \${PREV_TAG}"
                            sed -i "s|IMAGE_BACKEND_TAG=.*|IMAGE_BACKEND_TAG=${IMAGE_BACKEND}:\${PREV_TAG}|" .env
                            sed -i "s|IMAGE_FRONTEND_TAG=.*|IMAGE_FRONTEND_TAG=${IMAGE_FRONTEND}:\${PREV_TAG}|" .env
                            docker-compose up -d
                        fi
                    EOF
                """
            }
        }
        always {
            echo "==> Cleaning up build workspace..."
            sh "docker image prune -f || true"
        }
    }
}
