# Vault — Ultra-Secure Private Image Storage Platform

[![Security: Argon2id](https://img.shields.io/badge/Security-Argon2id-blue)](https://www.rfc-editor.org/rfc/rfc9106)
[![Architecture: Clean](https://img.shields.io/badge/Architecture-Clean%20Layered-emerald)](#architecture)
[![Testing: 100% Passed](https://img.shields.io/badge/Tests-16%20Passed-brightgreen)](#automated-testing)
[![Docker: Multi--Stage](https://img.shields.io/badge/Docker-Multi--Stage-blue)](#docker-deployment)
[![CI/CD: Jenkinsfile](https://img.shields.io/badge/CI%2FCD-Jenkins%20%2B%20Nexus%20%2B%20SonarQube-orange)](#enterprise-cicd-pipeline)

**Vault** is an enterprise-grade, multi-tenant private image-storage platform built with Python FastAPI, Next.js 14, PostgreSQL, and Nginx. Designed from inception with a **Zero-Trust Multi-Tenancy** architecture, every single image operation is strictly authenticated and authorized server-side to ensure absolute privacy between users.

---

## Key Features

- **Strict Multi-Tenant Isolation:** Complete protection against BOLA (Broken Object Level Authorization) and IDOR vulnerabilities. Requests to foreign images return generic non-leaking `404/403` responses.
- **Enterprise Cryptography:** Password hashing via **Argon2id** (RFC 9106 memory-hard parameters). Dual-token session authentication (15-min JWT access token + secure HTTPOnly SameSite refresh token rotation).
- **Hardened Ingestion Pipeline:** Pure magic byte / file signature verification (`\xff\xd8\xff`, `\x89PNG`, WebP, GIF), sensitive EXIF telemetry stripping (GPS, camera serials), path traversal neutralization, and non-executable storage permissions (`0600`).
- **Pluggable Storage Abstraction:** Abstract `StorageService` interface allowing effortless switching between local persistent volumes and S3/MinIO compatible object stores.
- **Instant WebP Thumbnails:** Automatic background-ready generation of WebP thumbnails for ultra-fast gallery scrolling.
- **Futuristic Cyber UI:** High-performance Next.js 14 frontend with drag-and-drop ingestion, progress tracking, fullscreen image viewer with keyboard navigation (`Left`/`Right`/`Esc`), album grouping, and metadata inspection.
- **Turnkey On-Premises CI/CD:** Ready for deployment across a 4-PC private data center cluster (Jenkins, SonarQube, Gitea, Nexus, Docker, PostgreSQL).

---

## System Architecture

```
Internet / LAN Users
         │
         ▼ (HTTPS / 443)
┌────────────────────────────────────────────────────────┐
│               PC 3: Nginx Reverse Proxy                │
│  - TLS Termination                                     │
│  - Brute-force rate limiting on auth endpoints         │
│  - Security headers (CSP, nosniff, DENY)               │
│  - 50MB client upload buffer                           │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
     ┌──────────────────────┐ ┌──────────────────────┐
     │  Next.js 14 Frontend │ │   FastAPI Backend    │
     │  (Port 3000)         │ │   (Port 8000)        │
     └──────────────────────┘ └──────────┬───────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│       PC 4: Central PostgreSQL       │    │      PC 3: Persistent Storage        │
│ - Database: vault                    │    │ - Directory: /data/images/users/...  │
│ - User: vault_app (isolated role)    │    │ - Mode: 0600 (Non-executable)        │
│ - Schema migrations via Alembic      │    │ - S3/MinIO compatible adapter        │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

---

## Quickstart — Local Development

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional for full containerized run)

### 2. Running the Backend Locally

```bash
cd vault/backend

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database setup (creates SQLite db or connects to PostgreSQL)
python3 init_db.py

# Start FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API documentation is accessible at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Running the Frontend Locally

```bash
cd vault/frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

The web application is accessible at: [http://localhost:3000](http://localhost:3000)

---

## Automated Testing

Vault includes a comprehensive automated test suite testing cross-user data isolation, IDOR defenses, authentication flows, MIME spoofing rejections, and storage traversal attacks.

```bash
cd vault/backend

# Execute full pytest suite with verbose output
python3 -m pytest tests/ -v
```

### Test Suite Highlights:
- `test_isolation_security.py`: Verifies that User B cannot `GET`, `DOWNLOAD`, `DELETE`, or `ADD TO ALBUM` any image uploaded by User A.
- `test_upload_validation.py`: Tests that executable/script payloads spoofed with image extensions are rejected (`422`), and directory traversal payloads (`../../etc/passwd.jpg`) are sanitized.
- `test_auth.py`: Tests Argon2id verification, duplicate prevention, and refresh token rotation with replay detection.
- `test_storage.py`: Tests path traversal defense in `LocalStorageService`.

---

## Docker Deployment (Docker Compose)

Run the entire multi-container production stack (PostgreSQL, FastAPI, Next.js, Nginx) locally or on a single node:

```bash
cd vault

# Copy environment variables template
cp .env.example .env

# Build and start all services
docker-compose up -d --build

# View container status and healthchecks
docker-compose ps

# View unified logs
docker-compose logs -f
```

The application is available on Port 80 (or configured `VAULT_PORT`).

---

## Enterprise CI/CD Pipeline (Jenkinsfile)

Vault includes a production `Jenkinsfile` for your 4-PC infrastructure:

1. **PC 1 (Jenkins + SonarQube):** Checks out code from Gitea, runs Bandit security audits, executes Pytest unit/isolation tests, verifies frontend build, and submits code quality analysis to SonarQube.
2. **PC 2 (Gitea + Nexus):** Builds versioned Docker images (`${BUILD_NUMBER}-${GIT_COMMIT}`) and pushes to Nexus Docker Registry (`nexus.internal:8082`).
3. **PC 4 (PostgreSQL):** Jenkins runs Alembic database migrations (`alembic upgrade head`) using isolated `vault_app` credentials.
4. **PC 3 (Application Runtime):** Jenkins SSHs to PC 3, pulls container images from Nexus, updates `.env`, restarts containers via `docker-compose up -d`, and polls `/health` for verification.
5. **Automatic Rollback:** If the health check fails after deployment, Jenkins automatically rolls back the runtime containers to the previous stable image tag.

---

## Documentation Index

- [Architecture & Design Blueprint](docs/architecture.md)
- [Security Model & Threat Defense](docs/security.md)
- [Database Schema & Provisioning Guide](docs/database.md)
- [4-PC Data Centre Deployment Guide](docs/deployment.md)

---

## Security & Production Checklist

### Pre-Deployment Checklist
- [x] Passwords hashed with memory-hard **Argon2id** (`argon2-cffi`).
- [x] Dual-token authentication with rotation on refresh.
- [x] Zero trust in frontend client `user_id` values.
- [x] All database queries scoped strictly by `owner_id`.
- [x] Magic byte signature inspection prevents extension spoofing.
- [x] EXIF telemetry stripped before disk storage.
- [x] Non-executable storage directory permissions (`0600`).
- [x] Path traversal attacks prevented via randomized UUID storage keys.
- [x] Rate limiting on authentication endpoints in Nginx.
- [x] Security headers enforced (`nosniff`, `DENY`, `CSP`, `Referrer-Policy`).
- [x] Database credentials decoupled from Gitea role.
- [x] Automated rollback configured in Jenkins pipeline.
