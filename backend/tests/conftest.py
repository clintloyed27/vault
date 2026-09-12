import app.compat  # noqa: F401
import io
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.storage.local import LocalStorageService
import app.storage as app_storage

# Use test SQLite in-memory DB
TEST_DATABASE_URL = "sqlite:///./test_vault.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


import app.db.session as db_session
import app.main as app_main

db_session.engine = test_engine
db_session.SessionLocal = TestingSessionLocal
app_main.engine = test_engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Setup test storage dir
    temp_storage = tempfile.mkdtemp(prefix="vault_test_storage_")
    settings.STORAGE_LOCAL_ROOT = temp_storage
    settings.DATABASE_URL = TEST_DATABASE_URL
    app_storage._storage_instance = LocalStorageService(root_dir=temp_storage)

    # Create tables
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    # Teardown
    Base.metadata.drop_all(bind=test_engine)
    shutil.rmtree(temp_storage, ignore_errors=True)
    import os
    if os.path.exists("./test_vault.db"):
        try:
            os.remove("./test_vault.db")
        except Exception:
            pass


@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def user_a_credentials():
    return {
        "email": "user_a@vault.internal",
        "password": "Password123!Secure",
        "full_name": "Alice Vault",
    }


@pytest.fixture
def user_b_credentials():
    return {
        "email": "user_b@vault.internal",
        "password": "Password456!Secure",
        "full_name": "Bob Vault",
    }


@pytest.fixture
def auth_header_user_a(client, user_a_credentials):
    # Register & Login User A
    client.post("/api/v1/auth/register", json=user_a_credentials)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": user_a_credentials["email"], "password": user_a_credentials["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_user_b(client, user_b_credentials):
    # Register & Login User B
    client.post("/api/v1/auth/register", json=user_b_credentials)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": user_b_credentials["email"], "password": user_b_credentials["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_jpeg_bytes():
    buf = io.BytesIO()
    img = PILImage.new("RGB", (640, 480), color=(30, 144, 255))
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes():
    buf = io.BytesIO()
    img = PILImage.new("RGBA", (300, 300), color=(255, 105, 180, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()
