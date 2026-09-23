# Server 2026 — Distributed Bare-Metal Data Center & Vault Platform Context

**Last Updated:** September 2026  
**Target Repository:** `https://github.com/clintloyed27/vault.git`  
**Gitea Repository:** `http://172.16.20.100:3000/root/server2026-test.git` (Branch: `main`)  
**Workspace Root:** `d:\Coding\server`

---

## 1. Executive Summary & Purpose

This document is the authoritative, definitive reference for the **Server 2026** enterprise infrastructure project. Any AI agent, model, or engineer joining this project must read and adhere to the architectural invariants, network topologies, credential structures, and DevSecOps constraints documented here.

### The Objective
Server 2026 is an on-premises, multi-node enterprise private-cloud infrastructure built on **Proxmox Virtual Environment (PVE)** across 4 physical bare-metal PCs. It hosts **Vault** — an ultra-secure, multi-tenant private image-storage platform built with FastAPI, Next.js 14, PostgreSQL, and Nginx.

### Fundamental Principle: Zero Manual Bypasses
The user explicitly mandates that **no manual terminal patching, base64 file injection, or ad-hoc container surgery be used to bypass the pipeline**. Everything running on this cluster must be built, analyzed, containerized, and deployed strictly through the automated DevSecOps CI/CD pipeline:
```
Developer Laptop (git push)
       │
       ▼
Gitea [PC2] (Source Control)
       │
       ▼ (Webhook / SCM Poll)
Jenkins [PC1] (CI/CD Pipeline Engine)
       ├─► 1. Checkout Code from Gitea
       ├─► 2. Security Audit (Bandit, Ruff, npm audit)
       ├─► 3. Unit & Isolation Tests (Pytest 16/16 Passed, Next.js build)
       ├─► 4. SonarQube Code Quality Analysis (PC1 :9000)
       ├─► 5. SonarQube Quality Gate Barrier
       ├─► 6. Docker Multi-Stage Image Build
       ├─► 7. Push Images to Nexus Docker Registry [PC2 :8082]
       ├─► 8. Apply Alembic DB Migrations to PostgreSQL [PC4 :5432]
       ├─► 9. Remote SSH Deployment via Docker Compose to [PC3]
       └─► 10. Automated Health Probe & Zero-Downtime Rollback Protection
```

---

## 2. Cluster Topology & Network Map

The cluster consists of 4 physical nodes on the subnet `172.16.20.0/24`:

```
                           ┌───────────────────────────────┐
                           │          PC 1: CI/CD          │
                           │       Proxmox: pve10          │
                           │       Host: 172.16.20.10      │
                           │   - Jenkins (Port 8080)       │
                           │   - SonarQube (Port 9000)     │
                           └───────────────┬───────────────┘
                                           │
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│     PC 2: STORAGE / REG       │ │    PC 3: APPLICATION HOST     │ │       PC 4: DATABASE          │
│       Proxmox: pve11          │ │       Proxmox: pve12          │ │       Proxmox: pve13          │
│       Host: 172.16.20.11      │ │       Host: 172.16.20.12      │ │       Host: 172.16.20.13      │
│   - Gitea (:3000 / .100)      │ │   - Docker Engine (ONLY HERE) │ │   - PostgreSQL 16 (:5432)     │
│   - Nexus Repo (:8081 / .103) │ │   - CT104 Nginx LXC (.104)    │ │   - Database: vault           │
│   - Nexus Docker Reg (:8082)  │ │   - CT105 FastAPI LXC (.105)  │ │   - User: vault_app           │
└───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

### Complete Address & Port Table

| Host / Node | Role | IP Address | Port(s) | Service / Description |
| :--- | :--- | :--- | :--- | :--- |
| **PC1 (`pve10`)** | CI / Automation | `172.16.20.10` | 8080 | Jenkins Automation Server |
| **PC1 (`pve10`)** | Code Quality | `172.16.20.102` / `172.16.20.10` | 9000 | SonarQube Community Edition |
| **PC2 (`pve11`)** | Source Control | `172.16.20.100` | 3000 | Gitea Git Web Service & API |
| **PC2 (`pve11`)** | Artifacts | `172.16.20.103` | 8081 | Nexus Repository Manager (Tarballs) |
| **PC2 (`pve11`)** | Container Registry | `172.16.20.103` | 8082 | Nexus Private Docker Hosted Registry |
| **PC3 (`pve12`)** | App Runtime Host | `172.16.20.12` | 22, 80, 8080 | Proxmox Host running Docker Engine |
| **PC3 (CT104)** | Ingress Proxy LXC | `172.16.20.104` | 80 | Standalone Ubuntu LXC with Nginx |
| **PC3 (CT105)** | Backend API LXC | `172.16.20.105` | 8000 | Standalone Ubuntu LXC with FastAPI (Python 3.12) |
| **PC4 (`pve13`)** | Database Engine | `172.16.20.13` | 5432 | Central PostgreSQL 16 Database Node |

---

## 3. Strict Architectural Invariants (DO NOT VIOLATE)

1. **Docker Engine Exists ONLY on PC3 (`172.16.20.12`)**:
   - PC1 (Jenkins) does NOT run production containers.
   - PC2 (Nexus) is a storage/registry backend, NOT a Docker runtime.
   - PC4 is strictly database storage.
   - Docker builds and Docker runs happen via remote deployment or within PC3.
2. **Never Create Dummy Containers (`app1`, `app2`)**:
   - Earlier debugging attempts mistakenly created `app1` and `app2`. These were deleted and must never be recreated.
3. **Never Move Services Across Physical PCs**:
   - Gitea stays on PC2.
   - PostgreSQL stays on PC4.
   - Jenkins stays on PC1.
   - Docker runtime stays on PC3.
4. **Never Bypass the CI/CD Pipeline**:
   - Do not manually edit `/var/www/html/` or `/etc/nginx/` inside containers via terminal pasting. All deployments must flow through Gitea -> Jenkins -> Nexus -> PC3.
5. **Console Prompt Disambiguation**:
   - `root@pve12:~#` = Physical Proxmox Hypervisor for PC3 (has Docker).
   - `root@FastAPI:~#` = CT105 LXC container on PC3 (Python runtime).
   - `root@Nginx:~#` = CT104 LXC container on PC3 (Nginx gateway).
   - `root@pve10:~#` = Physical Proxmox Hypervisor for PC1.
   - `root@pve11:~#` = Physical Proxmox Hypervisor for PC2.

---

## 4. The Production Application: Vault

The project running on this infrastructure is **Vault** (`https://github.com/clintloyed27/vault.git`), an enterprise-grade private image repository.

### Technology Stack
- **Backend:** Python 3.11+ / FastAPI, SQLAlchemy 2.0 ORM, Alembic migrations, Pydantic v2.
- **Frontend:** Next.js 14, React 18, Tailwind CSS, Lucide icons (plus standalone zero-dependency `preview.html` / `index.html` archival viewer).
- **Security:** Argon2id password hashing (`RFC 9106`), dual-token JWT auth (15-minute access + rotating HTTPOnly refresh tokens), strict BOLA/IDOR user isolation, magic byte file signature verification (`\xff\xd8\xff`, `\x89PNG`, WebP, GIF), EXIF metadata stripping, path traversal neutralization, and `0600` non-executable disk permissions.
- **Reverse Proxy:** Nginx 1.24+ with TLS termination, rate-limiting on auth endpoints (`15r/m`), CSP/nosniff security headers, and 50MB client payload buffers.
- **Database:** PostgreSQL 16 with UUID primary keys and foreign keys scoped to `owner_id`.

### Codebase Organization (`d:\Coding\server\`)
```
d:\Coding\server\
├── backend\
│   ├── alembic\                # Database migrations
│   ├── app\
│   │   ├── api\v1\             # REST endpoints (auth, users, images, albums, health)
│   │   ├── core\               # Configuration, security, logging, exceptions
│   │   ├── db\                 # SQLAlchemy engine and session factory
│   │   ├── models\             # Database ORM models (User, Image, Album)
│   │   ├── repositories\       # Data access layer (scoped strictly by owner_id)
│   │   ├── schemas\            # Pydantic validation schemas
│   │   ├── services\           # Business logic (auth, image validation, albums)
│   │   └── storage\            # Local & S3 storage abstraction (path-traversal defense)
│   ├── tests\                  # Pytest automated test suite (16 tests, 100% pass)
│   ├── Dockerfile              # Backend container definition
│   ├── requirements.txt        # Python production dependencies
│   └── init_db.py              # Schema bootstrapper
├── frontend\
│   ├── src\app\                # Next.js 14 App Router (gallery, login, register, albums)
│   ├── Dockerfile              # Next.js multi-stage production build
│   └── package.json            # Node.js dependencies
├── nginx\
│   └── nginx.conf              # Production reverse proxy configuration
├── docs\                       # Architecture, security, database & deployment blueprints
├── docker-compose.yml          # Production multi-tier stack definition
├── Jenkinsfile                 # 10-stage enterprise CI/CD pipeline
├── preview.html                # Interactive Vault archival print repository UI
├── index.html                  # Synced frontend view
├── test_e2e_live.py            # End-to-end integration verification suite
└── context.md                  # This file
```

### Backend Automated Test Suite
Vault includes a 16-test suite in `backend/tests/` verifying security isolation:
- `test_auth.py`: Registration, duplicate prevention, invalid login, refresh token rotation, invalid bearer tokens.
- `test_isolation_security.py`: Cross-user BOLA/IDOR isolation (User B cannot view, download, modify, or delete User A's images).
- `test_storage.py`: Directory traversal rejection (`../malicious`, `../../etc/passwd`), save/retrieve/delete verification.
- `test_upload_validation.py`: MIME spoofing rejection, corrupted image rejection, filename path traversal sanitization, thumbnail generation.
*Execution: `cd backend && python -m pytest tests/ -v` -> **16 PASSED** in ~3.0s.*

---

## 5. Jenkins DevSecOps Pipeline (`Jenkinsfile`)

The production pipeline in [Jenkinsfile](file:///d:/Coding/server/Jenkinsfile) defines 10 stages:

```groovy
pipeline {
    agent any
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }
    environment {
        NEXUS_REGISTRY    = credentials('nexus-registry-url')    // e.g. "172.16.20.103:8082"
        SONARQUBE_ENV     = 'SonarQube'                          // Configured in Jenkins
        DEPLOY_HOST       = '172.16.20.12'                       // PC3 host IP
        DB_HOST           = '172.16.20.13'                       // PC4 PostgreSQL IP
        IMAGE_BACKEND     = "${NEXUS_REGISTRY}/vault-backend"
        IMAGE_FRONTEND    = "${NEXUS_REGISTRY}/vault-frontend"
        IMAGE_TAG         = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
    }
    stages {
        stage('1. Checkout') { ... }
        stage('2. Security Lint & Static Analysis') { ... } // Bandit, Ruff, npm lint
        stage('3. Automated Testing Suite') { ... }        // Pytest (16 tests), npm build
        stage('4. SonarQube Code Quality Analysis') { ... } // sonar-scanner
        stage('5. Quality Gate Evaluation') { ... }         // waitForQualityGate()
        stage('6. Build & Tag Docker Images') { ... }       // multi-stage docker build
        stage('7. Push Images to Nexus Registry') { ... }   // docker push to :8082
        stage('8. Apply Database Migrations') { ... }       // alembic upgrade head on PC4
        stage('9. Deploy to Runtime Node (PC 3)') { ... }   // SSH to PC3, docker-compose up -d
        stage('10. Health Verification & Rollback') { ... } // curl /health with auto-rollback
    }
}
```

---

## 6. Credentials & Authentication Map

These credentials exist in Jenkins (`PC1:8080`) under System Credentials:

| Credential ID | Type | Description / Usage |
| :--- | :--- | :--- |
| `gitea-http` | Username with Password | Used by Jenkins to clone from Gitea (`172.16.20.100:3000`). Username: `root`. |
| `nexus-jenkins` / `nexus-registry-credentials` | Username with Password | Used to push/pull Docker images and artifacts to Nexus (`172.16.20.103`). |
| `sonarqube-token` | Secret Text | SonarQube authentication token for code quality analysis submissions. |
| `pve12-ssh` / `pc3-ssh-deploy-key` | SSH Username with Private Key | User `root` key for SSH remote deployment to PC3 (`172.16.20.12`). |
| `vault-postgres-credentials` | Username with Password | Database user (`vault_app`) and password for Alembic migrations on PC4. |

---

## 7. History of Failures, Discoveries & Resolutions

### Finding 1: The SSH Agent DSL Failure
- **Symptom:** Jenkins pipeline threw `No such DSL method 'sshagent'`.
- **Cause:** The Jenkins "SSH Agent Plugin" was not initially enabled.
- **Attempted Workaround:** Switched to `withCredentials([sshUserPrivateKey(...)])` which materialized the key to disk. This failed with OpenSSH `Load key "****": error in libcrypto / Permission denied`.
- **Fix:** Properly enabled the Jenkins SSH Agent plugin. In Build #24, `sshagent(['pve12-ssh'])` succeeded perfectly.

### Finding 2: SonarQube Quality Issues
- **Symptom:** SonarQube flagged errors in `index.html` (e.g., catching exceptions without logging or re-throwing) and Dockerfile security warnings (running as root).
- **Fix:** Handled exceptions cleanly with `console.error` and structured JSON error strings. Configured non-root user and strict immutability parameters (`USER nginx`, `--chmod=0444`).

### Finding 3: Proxmox Container IP Isolation vs. Docker Port Bindings
- **Symptom:** External browser received `ERR_CONNECTION_REFUSED` when visiting `http://172.16.20.12:80` even though `docker ps` showed the container up.
- **Cause:** Proxmox hypervisor firewall on `pve12` isolated the Docker bridge port from external LAN queries. However, LXC containers with designated LAN IPs (`172.16.20.104` for Nginx, `172.16.20.105` for FastAPI) are directly routable across the entire LAN.
- **Fix:** Production traffic routes through Nginx ingress (CT104 or Docker with host networking).

### Finding 4: The Terminal Line-Wrapping Corruption Trap
- **Symptom:** Trying to paste multi-line HTML or scripts into interactive terminal sessions (`root@Nginx:~#`) resulted in truncated lines and corrupted files (HTTP 404).
- **Rule:** Never paste raw multi-line code directly into SSH consoles. Always use version control (`git push`), Docker Compose, or clean single-line base64 decoders.

### Finding 5: Nginx Worker socketpair() Failure on Proxmox Hypervisor
- **Symptom:** In Build #32–#35, Nginx in Docker started but requests timed out (`Read timed out`). Container logs showed:
  `[alert] 1#1: socketpair() failed while spawning "worker process" (13: Permission denied)`.
- **Cause:** On Proxmox host kernels, unprivileged process capability restrictions prevented Nginx master from executing `socketpair()` to create IPC channels for worker processes. No workers could be spawned to handle connections.
- **Fix:** Configured `master_process off;` in `/etc/nginx/nginx.conf` and mapped `-p 8080:80` with `--privileged`. Nginx runs cleanly in single-process mode, serving requests instantly.

---

## 8. Verified Live Deployment (Build #36)

The entire automated CI/CD loop has completed with **SUCCESS**:

1. **Source Code:** Vault codebase pushed to Gitea (`http://172.16.20.100:3000/root/server2026-test.git`).
2. **CI Automation:** Jenkins on PC1 (`http://172.16.20.101:8080`) checked out commit `daa1c2c`, performed SonarQube quality analysis (`http://172.16.20.102:9000`), packaged the build artifact, and uploaded it to Nexus (`http://172.16.20.103:8081`).
3. **Container Delivery:** PC3 built the production container `server2026-test:36` with `--no-cache`, pushed it to Nexus Docker Registry (`172.16.20.103:8082`), and deployed container `server2026-web`.
4. **Live Verification:** HTTP probe returned **HTTP/1.1 200 OK** (`Content-Length: 42153`).
5. **Live URL:** **`http://172.16.20.12:8080`** (Accessible from all machines on the `172.16.20.0/24` LAN).

