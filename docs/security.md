# Vault Security Architecture & Threat Model

Security is treated as a foundational requirement in Vault. The application is built under a **Zero-Trust Multi-Tenant** security model.

---

## 1. Authentication & Session Management

### A. Argon2id Password Hashing
- Algorithm: **Argon2id** (RFC 9106 recommended parameters)
- Memory cost: 64 MB (`memory_cost=65536`)
- Time cost: 3 iterations (`time_cost=3`)
- Parallelism: 4 threads (`parallelism=4`)
- Salts: 16 bytes cryptographically secure random bytes generated per hash.
- Mitigates GPU-accelerated hash cracking and ASIC attacks.

### B. Dual-Token Architecture
- **Access Token:** Short-lived JWT (15 minutes). Sent in the `Authorization: Bearer <token>` header. Contains standard claims (`sub: user_id`, `exp`, `iat`, `type: access`).
- **Refresh Token:** Cryptographically random 64-character token (`secrets.token_urlsafe(64)`).
  - Stored only as a SHA-256 hash in the database to prevent token extraction if the database is dumped.
  - Transmitted in an `HTTPOnly`, `SameSite=Lax`, `Secure` cookie scoped to `/api/v1/auth`.
  - **Token Rotation:** Every refresh request invalidates the old token and issues a new pair. If an already-used refresh token is presented, all user sessions are immediately revoked (replay attack defense).

---

## 2. Multi-Tenant Isolation & BOLA/IDOR Defense

### The Golden Rule: Zero Client Trust
The backend never trusts a `user_id` supplied in request bodies, URL paths, or headers.

1. **Identity Derivation:** The authenticated tenant's identity is derived strictly from the cryptographically verified JWT access token via `get_current_user`.
2. **Repository-Level Filtering:** Every database query explicitly scopes by `owner_id = current_user.id`.
3. **Non-Leaking Error Codes:**
   - When User B requests an image belonging to User A (`GET /api/v1/images/{image_a_id}`), the repository returns `None`.
   - The backend logs a security audit violation and returns `404 Not Found` or `403 Forbidden` without revealing the filename, existence, or owner of the resource.
4. **Album Isolation:** Adding images to albums strictly verifies that both the album and every single image belong to the current authenticated tenant.

---

## 3. Upload & File Ingestion Security

### A. Magic Byte Inspection (Anti-Spoofing)
File extensions sent by the client are never trusted. The backend inspects leading magic bytes:
- `\xFF\xD8\xFF` -> `image/jpeg`
- `\x89PNG\r\n\x1a\n` -> `image/png`
- `GIF87a` / `GIF89a` -> `image/gif`
- `RIFF....WEBP` -> `image/webp`

Any payload that fails signature validation (e.g. `script.py.jpg` containing bash or Python scripts) is rejected immediately with `422 Unprocessable Content`.

### B. EXIF Sanitization
- Uploaded images are decompressed and re-encoded using Pillow.
- Dangerous EXIF metadata (GPS coordinates, camera device IDs, location telemetry) is stripped before writing to disk.
- Safe technical attributes (width, height, format, color mode) are stored as JSON in PostgreSQL.

### C. Path Traversal & Identifier Randomization
- User input is never used as a filesystem path.
- Files are saved with server-generated random UUID v4 identifiers (`<uuid>.jpg`).
- The `LocalStorageService` verifies that paths do not contain traversal sequences (`..`, `/`, `\\`) and verifies that resolved paths reside strictly inside the user's isolated directory (`Path.resolve().startswith(...)`).

### D. Non-Executable Storage
- Files are written with restricted permissions (`0600` for files, `0700` for directories).
- Web servers cannot execute or directly browse stored files.

---

## 4. Network & Ingress Hardening

### A. Rate Limiting (Nginx)
The Nginx ingress proxy establishes a memory zone tracking client IPs:
```nginx
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=15r/m;
```
Applied to `/api/v1/auth/login` to prevent automated brute-force attacks.

### B. Security Headers
Both FastAPI middleware and Nginx inject defense-in-depth HTTP headers:
- `X-Frame-Options: DENY` (Anti-clickjacking)
- `X-Content-Type-Options: nosniff` (Anti-MIME sniffing)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (In production)
- `Content-Security-Policy: default-src 'self' ...`
