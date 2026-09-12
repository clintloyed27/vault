# Vault System Architecture

Vault is a production-grade, multi-tenant private image storage platform engineered for on-premises deployment in an enterprise private data centre.

---

## 1. High-Level Component Topology

```
+-------------------------------------------------------------------------------+
|                            Client (Browser / Mobile)                         |
+-------------------------------------------------------------------------------+
                                        | (HTTPS / 443)
                                        v
+-------------------------------------------------------------------------------+
|                   PC 3: Nginx Reverse Proxy (Ingress Gateway)                |
|  - TLS Termination                                                            |
|  - Content Security Policy & Security Headers (nosniff, DENY)                 |
|  - Rate-limiting zone on /api/v1/auth/ (Brute force protection)               |
|  - Max Body Size: 50MB (buffer high-res photo streams)                        |
+-------------------------------------------------------------------------------+
           |                                                    |
           v                                                    v
+-----------------------+                            +-----------------------+
| PC 3: Next.js Frontend|                            | PC 3: FastAPI Backend |
|  - React 18, TS       |                            |  - Clean Architecture |
|  - Standalone Node    |                            |  - Argon2id Auth      |
|  - Cyber Vault UI     |                            |  - Multi-Tenant AuthZ |
+-----------------------+                            +-----------------------+
                                                                |
                                        +-----------------------+-----------------------+
                                        |                                               |
                                        v                                               v
+-----------------------------------------------+   +-----------------------------------------------+
|         PC 4: Central PostgreSQL              |   |          PC 3: Persistent Storage             |
|  - Database: vault                            |   |  - Isolated directory per user UUID           |
|  - User: vault_app (Non-Gitea role)           |   |  - Non-executable permissions (0600)          |
|  - Relational metadata, hashes, foreign keys  |   |  - Hot-swappable to MinIO / S3                |
+-----------------------------------------------+   +-----------------------------------------------+
```

---

## 2. Layered Clean Architecture (Backend)

The FastAPI application is strictly separated into independent layers:

```
[API Layer] (app/api/v1/)
   └── HTTP request validation, query parameter parsing, dependency injection
           ↓
[Service Layer] (app/services/)
   └── Business logic, Argon2id auth, MIME inspection, EXIF stripping, thumbnailing
           ↓
[Repository Layer] (app/repositories/)
   └── SQL queries strictly scoped by owner_id (Zero-trust tenancy)
           ↓
[Storage Abstraction] (app/storage/)
   └── Abstract StorageService -> LocalStorageService / S3StorageService
           ↓
[Database Layer] (app/models/ & app/db/)
   └── SQLAlchemy Declarative ORM models & Alembic migrations
```

---

## 3. Storage Abstraction Layer

The application interacts with persistent image blobs exclusively via the abstract `StorageService` interface:

```python
class StorageService(ABC):
    def save_file(self, user_id: str, file_key: str, data: bytes) -> str: ...
    def get_file_stream(self, user_id: str, file_key: str) -> Generator[bytes, None, None]: ...
    def get_file_bytes(self, user_id: str, file_key: str) -> bytes: ...
    def delete_file(self, user_id: str, file_key: str) -> bool: ...
    def file_exists(self, user_id: str, file_key: str) -> bool: ...
```

### Local Storage Layout
- Root: `/data/images/users/<user_uuid>/`
- Original Image: `<image_uuid>.jpg`
- Thumbnail: `<image_uuid>_thumb.webp`
- Path traversal defense: All paths are checked using strict string validation against `..`, `/`, `\\` before resolution.
- Permissions: Directory `0700`, Files `0600`.
- **Zero Public Direct Access:** The storage directory is never mounted or exposed to Nginx or the web; all requests are authenticated and streamed by FastAPI.

---

## 4. Scalability & Evolution Roadmap

1. **Local Disk -> MinIO Object Storage:** By setting `STORAGE_TYPE=s3`, the application switches seamlessly to an S3-compatible cluster (Ceph, MinIO, or AWS S3).
2. **Synchronous -> Background Workers:** As upload volume increases, thumbnail generation can be offloaded to Celery/Redis without altering frontend upload contracts.
3. **Client-Side Zero-Knowledge Encryption:** Designed with a clean metadata schema to allow client-side AES-256-GCM encryption before payload ingestion.
