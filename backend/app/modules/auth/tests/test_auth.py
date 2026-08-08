"""
Tests for Auth module.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient) -> None:
    """Test clinician registration and subsequent login."""
    # 1. Register
    reg_payload = {
        "first_name": "Sarah",
        "last_name": "Connor",
        "email": "sarah.connor@hospital.org",
        "password": "SecurePassword123!",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()["data"]
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == "sarah.connor@hospital.org"

    # 2. Login
    login_payload = {
        "email": "sarah.connor@hospital.org",
        "password": "SecurePassword123!",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()["data"]
    assert "access_token" in login_data

    # 3. Get /me
    headers = {"Authorization": f"Bearer {login_data['access_token']}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200, me_resp.text
    assert me_resp.json()["data"]["email"] == "sarah.connor@hospital.org"


@pytest.mark.asyncio
async def test_duplicate_registration_fails(async_client: AsyncClient) -> None:
    """Ensure registering with an existing email returns 409 Conflict."""
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@hospital.org",
        "password": "Password123!",
    }
    resp1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
