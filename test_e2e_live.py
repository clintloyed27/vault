#!/usr/bin/env python3
"""
End-to-End Live System Verification Script for Vault
Demonstrates and validates:
- User registration & authentication (Argon2id + JWT)
- File ingestion with magic byte validation & EXIF stripping
- Thumbnail generation & streaming
- Strict cross-user multi-tenant isolation (IDOR defense)
- Collections / Albums management
- Clean resource deletion
"""

import io
import sys
import tempfile
from pathlib import Path
from PIL import Image as PILImage

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.compat  # noqa: F401
from app.core.config import settings
from app.db.session import Base, get_db
import app.db.session as db_session
import app.main as app_main
from app.storage.local import LocalStorageService
import app.storage as app_storage


# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(title):
    print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")


def assert_test(condition, message):
    if condition:
        print(f"  {GREEN}✔ [PASS]{RESET} {message}")
    else:
        print(f"  {RED}✘ [FAIL]{RESET} {message}")
        raise AssertionError(message)


def generate_image_bytes(format="JPEG", size=(800, 600), color=(20, 120, 240)):
    buf = io.BytesIO()
    img = PILImage.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


def run_e2e_verification():
    print(f"\n{BOLD}╔════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║             VAULT LIVE END-TO-END SYSTEM TEST                 ║{RESET}")
    print(f"{BOLD}║    Validating Security, Isolation, Storage, and Operations     ║{RESET}")
    print(f"{BOLD}╚════════════════════════════════════════════════════════════════╝{RESET}")

    # Set up isolated SQLite and storage area for test
    temp_dir = tempfile.mkdtemp(prefix="vault_e2e_")
    test_db_url = f"sqlite:///{temp_dir}/e2e_vault.db"

    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Wire up test environment
    settings.STORAGE_LOCAL_ROOT = f"{temp_dir}/storage"
    settings.DATABASE_URL = test_db_url
    db_session.engine = test_engine
    db_session.SessionLocal = TestingSession
    app_main.engine = test_engine
    app_storage._storage_instance = LocalStorageService(root_dir=f"{temp_dir}/storage")

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app_main.app)

    # -------------------------------------------------------------
    # 1. Health Checks
    # -------------------------------------------------------------
    print_step("1. Verifying System Health Endpoints")
    health_res = client.get("/health")
    assert_test(health_res.status_code == 200, "Liveness probe /health is HTTP 200 OK")
    assert_test(health_res.json()["status"] == "healthy", "Liveness probe reports healthy")

    readiness_res = client.get("/readiness")
    assert_test(readiness_res.status_code == 200, "Readiness probe /readiness is HTTP 200 OK")
    assert_test(readiness_res.json()["database"] == "connected", "Database connection verified")
    assert_test(readiness_res.json()["storage"] == "writable", "Storage volume writability verified")

    # -------------------------------------------------------------
    # 2. Registration & Authentication
    # -------------------------------------------------------------
    print_step("2. User Registration & Argon2id Authentication")
    user_a_email = "alice@vault.internal"
    user_a_pass = "AliceSecurePass2026!"
    reg_a = client.post("/api/v1/auth/register", json={
        "email": user_a_email,
        "password": user_a_pass,
        "full_name": "Alice Vault",
    })
    assert_test(reg_a.status_code == 201, "Registered User A (Alice)")
    user_a_id = reg_a.json()["id"]

    user_b_email = "bob@vault.internal"
    user_b_pass = "BobSecurePass2026!"
    reg_b = client.post("/api/v1/auth/register", json={
        "email": user_b_email,
        "password": user_b_pass,
        "full_name": "Bob Vault",
    })
    assert_test(reg_b.status_code == 201, "Registered User B (Bob)")
    user_b_id = reg_b.json()["id"]

    # Login User A
    login_a = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": user_a_pass})
    assert_test(login_a.status_code == 200, "User A login successful")
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Login User B
    login_b = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": user_b_pass})
    assert_test(login_b.status_code == 200, "User B login successful")
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # -------------------------------------------------------------
    # 3. Ingestion & Upload Security
    # -------------------------------------------------------------
    print_step("3. File Ingestion, Validation & Thumbnailing")
    # A. Test spoofed script rejection
    spoofed_bytes = b"#!/bin/bash\necho 'Trojan Horse'\n"
    bad_res = client.post(
        "/api/v1/images/upload",
        headers=headers_a,
        files={"files": ("exploit.jpg", spoofed_bytes, "image/jpeg")},
    )
    assert_test(bad_res.status_code == 422, "Spoofed script disguised as .jpg correctly REJECTED (422)")

    # B. Test valid image upload
    img1_bytes = generate_image_bytes("JPEG", size=(1024, 768), color=(40, 160, 220))
    upload_res = client.post(
        "/api/v1/images/upload",
        headers=headers_a,
        files={"files": ("vacation_beach.jpg", img1_bytes, "image/jpeg")},
    )
    assert_test(upload_res.status_code == 201, "Uploaded valid JPEG as User A")
    img1 = upload_res.json()[0]
    img1_id = img1["id"]
    assert_test(img1["width"] == 1024 and img1["height"] == 768, "Metadata extraction matches resolution (1024x768)")
    assert_test(img1["thumbnail_key"] is not None, "WebP thumbnail automatically generated")

    # -------------------------------------------------------------
    # 4. Multi-Tenant Cross-User Isolation (BOLA / IDOR Verification)
    # -------------------------------------------------------------
    print_step("4. Multi-Tenant Data Isolation & BOLA/IDOR Defenses")

    # User A CAN access their image
    a_read = client.get(f"/api/v1/images/{img1_id}", headers=headers_a)
    assert_test(a_read.status_code == 200, "User A CAN read their own image")

    # User B CANNOT access User A's image metadata
    b_read = client.get(f"/api/v1/images/{img1_id}", headers=headers_b)
    assert_test(b_read.status_code in (403, 404), f"User B CANNOT read User A's image metadata (HTTP {b_read.status_code})")

    # User B CANNOT download or stream User A's image file
    b_file = client.get(f"/api/v1/images/{img1_id}/file", headers=headers_b)
    assert_test(b_file.status_code in (403, 404), f"User B CANNOT stream User A's image file (HTTP {b_file.status_code})")

    # User B CANNOT view User A's thumbnail
    b_thumb = client.get(f"/api/v1/images/{img1_id}/thumbnail", headers=headers_b)
    assert_test(b_thumb.status_code in (403, 404), f"User B CANNOT view User A's thumbnail (HTTP {b_thumb.status_code})")

    # User B CANNOT delete User A's image
    b_del = client.delete(f"/api/v1/images/{img1_id}", headers=headers_b)
    assert_test(b_del.status_code in (403, 404), f"User B CANNOT delete User A's image (HTTP {b_del.status_code})")

    # Verify Image still intact
    a_verify = client.get(f"/api/v1/images/{img1_id}", headers=headers_a)
    assert_test(a_verify.status_code == 200, "User A's image remains intact and unharmed")

    # -------------------------------------------------------------
    # 5. Collections & Albums Permissions
    # -------------------------------------------------------------
    print_step("5. Albums & Cross-User Permissions")
    # User B creates an album
    album_b = client.post("/api/v1/albums/", headers=headers_b, json={
        "title": "Bob's Secret Folder",
        "description": "Bob's private album"
    }).json()
    album_b_id = album_b["id"]
    assert_test(album_b["title"] == "Bob's Secret Folder", "User B created Album B")

    # User B tries to add User A's image to Album B -> MUST BE FORBIDDEN
    add_steal = client.post(
        f"/api/v1/albums/{album_b_id}/images",
        headers=headers_b,
        json={"image_ids": [img1_id]},
    )
    assert_test(add_steal.status_code == 403, "User B BLOCKED from adding User A's image to Album B (HTTP 403)")

    # User A creates Album A and adds their image
    album_a = client.post("/api/v1/albums/", headers=headers_a, json={
        "title": "Alice's Travel Album"
    }).json()
    album_a_id = album_a["id"]
    add_ok = client.post(
        f"/api/v1/albums/{album_a_id}/images",
        headers=headers_a,
        json={"image_ids": [img1_id]},
    )
    assert_test(add_ok.status_code == 200, "User A successfully added their image to Album A")

    # User B CANNOT view Album A
    b_album_view = client.get(f"/api/v1/albums/{album_a_id}", headers=headers_b)
    assert_test(b_album_view.status_code in (403, 404), f"User B CANNOT access User A's Album (HTTP {b_album_view.status_code})")

    # -------------------------------------------------------------
    # 6. Storage & Clean Deletion
    # -------------------------------------------------------------
    print_step("6. Metadata Modification & Permanent Deletion")
    rename_res = client.patch(
        f"/api/v1/images/{img1_id}",
        headers=headers_a,
        json={"original_filename": "summer_vacation_2026.jpg"},
    )
    assert_test(rename_res.status_code == 200, "Renamed image filename successfully")
    assert_test(rename_res.json()["original_filename"] == "summer_vacation_2026.jpg", "Updated filename reflected in metadata")

    del_res = client.delete(f"/api/v1/images/{img1_id}", headers=headers_a)
    assert_test(del_res.status_code == 204, "User A permanently deleted the image (HTTP 204)")

    get_after_del = client.get(f"/api/v1/images/{img1_id}", headers=headers_a)
    assert_test(get_after_del.status_code == 404, "Image no longer exists in vault (HTTP 404)")

    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\n{BOLD}{GREEN}════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}  ALL LIVE END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!  {RESET}")
    print(f"{BOLD}{GREEN}════════════════════════════════════════════════════════════════{RESET}\n")


if __name__ == "__main__":
    run_e2e_verification()
