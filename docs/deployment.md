# Vault Private Data Centre Deployment Guide

This guide details how to integrate and deploy Vault into your 4-PC enterprise on-premises architecture.

---

## 1. Infrastructure Topology Mapping

```
+-------------------+      +-------------------+
|       PC 1        |      |       PC 2        |
| Jenkins Master/Worker    | Gitea Git Server  |
| SonarQube Server  |      | Nexus Registry    |
+-------------------+      +-------------------+
          |                          |
          v                          v
+-------------------+      +-------------------+
|       PC 3        |      |       PC 4        |
| Application Host  |<---->| Central PostgreSQL|
| Docker + Nginx    |      | (Database: vault) |
| Local Storage     |      |                   |
+-------------------+      +-------------------+
```

### Node Responsibilities
- **PC 1 (CI/CD Engine):**
  - Jenkins executes builds, tests, security audits, and deployment triggers.
  - SonarQube evaluates code quality and gates pipeline execution.
- **PC 2 (Source & Artifacts):**
  - Gitea hosts the Git repository and notifies Jenkins via webhooks.
  - Nexus Registry (`nexus.internal:8082`) stores versioned Docker images (`vault-backend`, `vault-frontend`).
- **PC 3 (Application Runtime):**
  - Runs the containerized application stack (`vault-backend`, `vault-frontend`, `vault-nginx`).
  - Hosts the persistent storage mount (`/data/images`).
- **PC 4 (Central Database):**
  - Dedicated PostgreSQL instance hosting the `vault` database and `vault_app` user.

---

## 2. Firewall & Port Allocation Matrix

| Node | Service | Port | Protocol | Source Permitted |
| :--- | :--- | :--- | :--- | :--- |
| **PC 1** | Jenkins UI | 8080 | HTTP | LAN / Admin |
| **PC 1** | SonarQube | 9000 | HTTP | PC 1 (Jenkins) |
| **PC 2** | Gitea | 3000 / 22 | HTTP / SSH | LAN / Developers |
| **PC 2** | Nexus Registry | 8082 | HTTP / HTTPS | PC 1, PC 3 |
| **PC 3** | Nginx Ingress | 80 / 443 | HTTP / HTTPS | Public / LAN Users |
| **PC 3** | SSH Deployment | 22 | SSH | PC 1 (Jenkins worker only) |
| **PC 4** | PostgreSQL | 5432 | TCP | PC 1 (Migrations), PC 3 (Backend) |

> [!CAUTION]
> PostgreSQL (Port 5432) and the image storage filesystem must NEVER be exposed publicly or reachable from outside the secure LAN.

---

## 3. Jenkins Credentials Setup (PC 1)

In the Jenkins Web UI (`Manage Jenkins -> Credentials -> System -> Global credentials`), add the following:

1. **`nexus-registry-url`** (Secret text):
   - Value: `192.168.1.102:8082` (Hostname/IP of PC 2 Nexus Docker connector)
2. **`nexus-registry-credentials`** (Username with password):
   - Username: `jenkins-deployer`
   - Password: `<nexus_secure_password>`
3. **`pc3-ssh-deploy-key`** (SSH Username with private key):
   - Username: `vault-deploy`
   - Private Key: RSA/ED25519 private key authorized on PC 3 in `/home/vault-deploy/.ssh/authorized_keys`
4. **`vault-postgres-credentials`** (Username with password):
   - Username: `vault_app`
   - Password: `<central_pg_password>`
5. **`vault-secret-key`** (Secret text):
   - Value: 48-byte cryptographically random string (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`)

---

## 4. Runtime Node Provisioning (PC 3)

Run the following one-time setup on PC 3:

```bash
# 1. Create deployment user and folders
sudo useradd -m -s /bin/bash vault-deploy
sudo usermod -aG docker vault-deploy

# 2. Create persistent image storage directory with secure non-root permissions
sudo mkdir -p /data/images
sudo chown -R 10001:10001 /data/images
sudo chmod -R 700 /data/images

# 3. Create deployment configuration directory
sudo mkdir -p /opt/vault
sudo chown -R vault-deploy:vault-deploy /opt/vault
```

---

## 5. Deployment Lifecycle & Automated Rollback

When a developer pushes to Gitea:
1. Gitea fires a webhook triggering Jenkins on PC 1.
2. Jenkins checks out code, runs Python security scans (`bandit`), runs backend Pytest unit tests, and tests frontend compilation.
3. SonarQube runs static analysis.
4. Jenkins builds multi-stage Docker images, tags them with `${BUILD_NUMBER}-${GIT_COMMIT}`, and pushes to Nexus on PC 2.
5. Jenkins executes database migrations against PC 4 (`alembic upgrade head`).
6. Jenkins SSHs to PC 3, pulls the new container tags from Nexus, records the previous stable tag to `/opt/vault/previous_tag.txt`, and triggers `docker-compose up -d`.
7. Jenkins polls `http://PC3_HOST/health` for 60 seconds.
   - **Success:** Notifies success and preserves new tag.
   - **Failure:** Automatically invokes rollback post-action, restoring the previous stable image tag on PC 3.
