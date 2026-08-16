"""
tests/integration/test_auth.py
-------------------------------
Integration tests for user registration, authentication, and current-user endpoints.
"""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecretPassword123!"

    # 1. Register
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Integration User", "email": email, "password": password},
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == email
    assert "id" in user_data

    # 2. Login
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data

    token = token_data["access_token"]

    # 3. GET /me
    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, create_user):
    dup_email = f"dup_{uuid.uuid4().hex[:6]}@example.com"
    user = await create_user(email=dup_email)

    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Dup", "email": dup_email, "password": "password123"},
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient, create_user):
    user_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    user = await create_user(email=user_email, password="password123")

    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "wrongpassword"},
    )
    assert resp.status_code == 400
    assert "Invalid email or password" in resp.json()["detail"]
