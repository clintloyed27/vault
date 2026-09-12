# Vault Database Architecture & Provisioning Guide

Vault utilizes PostgreSQL 16+ as its central metadata store.

> [!IMPORTANT]
> **Database Isolation:** Vault requires its own dedicated database (`vault`) and non-superuser role (`vault_app`). It MUST NOT share a database user or schema with Gitea or any other service.

---

## 1. Database Provisioning on PC 4 (Central DB Server)

Before running migrations or launching the Vault application in production, run the following SQL commands on your central PostgreSQL cluster (PC 4):

```sql
-- 1. Create dedicated application role with strong password
CREATE USER vault_app WITH ENCRYPTED PASSWORD 'generate_a_secure_database_password_here';

-- 2. Create the Vault database
CREATE DATABASE vault WITH OWNER vault_app ENCODING 'UTF8';

-- 3. Grant schema permissions
\c vault
GRANT ALL PRIVILEGES ON SCHEMA public TO vault_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO vault_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO vault_app;

-- 4. Enable pg_crypto extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

---

## 2. Relational Schema Specification

### A. `users` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK | Tenant UUID |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | Primary login identifier |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Argon2id hash |
| `full_name` | `VARCHAR(255)` | NULL | Display name |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT true | Account status flag |
| `is_superuser` | `BOOLEAN` | NOT NULL, DEFAULT false | Administrative flag |
| `created_at` | `TIMESTAMPTZ`| NOT NULL | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ`| NOT NULL | Last update timestamp |

### B. `images` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK | Image UUID |
| `owner_id` | `VARCHAR(36)` | FK(`users.id` ON DELETE CASCADE), INDEX | Tenant owner |
| `storage_key` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | Random disk identifier |
| `thumbnail_key`| `VARCHAR(255)` | NULL | Thumbnail disk identifier |
| `original_filename`| `VARCHAR(255)`| NOT NULL | Sanitized display name |
| `mime_type` | `VARCHAR(100)` | NOT NULL | Verified MIME type |
| `file_size` | `BIGINT` | NOT NULL | Size in bytes |
| `width` | `INTEGER` | NULL | Pixel width |
| `height` | `INTEGER` | NULL | Pixel height |
| `checksum_sha256` | `VARCHAR(64)` | NOT NULL, INDEX | Payload SHA-256 hash |
| `metadata_json` | `JSON` | NULL | Safe extracted metadata |
| `created_at` | `TIMESTAMPTZ`| NOT NULL, INDEX | Upload timestamp |
| `updated_at` | `TIMESTAMPTZ`| NOT NULL | Last modified timestamp |

### C. `albums` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK | Album UUID |
| `owner_id` | `VARCHAR(36)` | FK(`users.id` ON DELETE CASCADE), INDEX | Tenant owner |
| `title` | `VARCHAR(255)` | NOT NULL | Collection name |
| `description`| `TEXT` | NULL | Collection description |
| `cover_image_id`| `VARCHAR(36)`| FK(`images.id` ON DELETE SET NULL) | Optional album cover |
| `created_at` | `TIMESTAMPTZ`| NOT NULL | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ`| NOT NULL | Update timestamp |

### D. `album_images` Table (Junction)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `album_id` | `VARCHAR(36)` | PK, FK(`albums.id` ON DELETE CASCADE) | Album reference |
| `image_id` | `VARCHAR(36)` | PK, FK(`images.id` ON DELETE CASCADE) | Image reference |
| `added_at` | `TIMESTAMPTZ`| NOT NULL | Time linked to album |

### E. `refresh_tokens` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK | Token record UUID |
| `user_id` | `VARCHAR(36)` | FK(`users.id` ON DELETE CASCADE), INDEX | User reference |
| `token_hash`| `VARCHAR(64)` | UNIQUE, NOT NULL, INDEX | SHA-256 hash of token |
| `expires_at`| `TIMESTAMPTZ`| NOT NULL | Token expiry time |
| `is_revoked`| `BOOLEAN` | NOT NULL, DEFAULT false | Invalidation flag |
| `created_at`| `TIMESTAMPTZ`| NOT NULL | Issuance timestamp |

---

## 3. Database Migration Procedures

### Applying Migrations via Alembic
```bash
cd backend
export POSTGRES_SERVER=192.168.1.104
export POSTGRES_USER=vault_app
export POSTGRES_PASSWORD=your_secure_password
export POSTGRES_DB=vault

# Run all pending migrations
alembic upgrade head
```

### Standalone Migration / Schema Init
If running without the Alembic CLI:
```bash
cd backend
python3 init_db.py
```

### Creating New Schema Revisions
```bash
cd backend
alembic revision -m "add_new_feature"
```

---

## 4. Backup & Disaster Recovery

### Creating a Database Backup
```bash
pg_dump -h 192.168.1.104 -U vault_app -Fc vault > /backups/vault_db_$(date +%Y%m%d_%H%M%S).dump
```

### Restoring from Backup
```bash
pg_restore -h 192.168.1.104 -U vault_app -d vault --clean --if-exists /backups/vault_db_backup.dump
```
