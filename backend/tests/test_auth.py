import pytest
from app.core.security import verify_password


def test_register_and_login_success(client):
    register_data = {
        "email": "fresh_user@vault.internal",
        "password": "StrongPassword2026!",
        "full_name": "Test User",
    }
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json=register_data)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "fresh_user@vault.internal"
    assert user_data["full_name"] == "Test User"
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # 2. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": register_data["email"], "password": register_data["password"]},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert "vault_refresh_token" in login_res.cookies


def test_duplicate_registration_rejected(client, user_a_credentials):
    # Register first time
    client.post("/api/v1/auth/register", json=user_a_credentials)
    # Register second time with duplicate email
    res = client.post("/api/v1/auth/register", json=user_a_credentials)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"].lower()


def test_login_invalid_password(client, user_a_credentials):
    client.post("/api/v1/auth/register", json=user_a_credentials)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": user_a_credentials["email"], "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "incorrect" in res.json()["detail"].lower()


def test_login_nonexistent_user(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@vault.internal", "password": "AnyPassword123!"},
    )
    assert res.status_code == 401


def test_refresh_token_rotation(client, user_a_credentials):
    client.post("/api/v1/auth/register", json=user_a_credentials)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user_a_credentials["email"], "password": user_a_credentials["password"]},
    )
    cookie_token = login_res.cookies.get("vault_refresh_token")
    assert cookie_token is not None

    # Call refresh
    refresh_res = client.post("/api/v1/auth/refresh", cookies={"vault_refresh_token": cookie_token})
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data

    # Verify old refresh token was revoked (reuse detection)
    stale_res = client.post("/api/v1/auth/refresh", cookies={"vault_refresh_token": cookie_token})
    assert stale_res.status_code == 401


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/v1/images/")
    assert res.status_code == 401


def test_invalid_bearer_token(client):
    res = client.get(
        "/api/v1/images/",
        headers={"Authorization": "Bearer forged.invalid.token.signature"},
    )
    assert res.status_code == 401
