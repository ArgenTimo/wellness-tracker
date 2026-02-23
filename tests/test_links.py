"""Tests for links (invites, redeem) and access model."""

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str, password: str) -> dict | None:
    """Login and return Authorization header."""
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    if r.status_code != 200:
        return None
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, email: str, password: str) -> dict:
    """Register user, return response json."""
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_redeem_self_link_does_nothing(client: AsyncClient):
    """Redeeming own invite returns ignored_self_redeem."""
    await _register(client, "self@test.com", "password123")
    headers = await _auth_headers(client, "self@test.com", "password123")
    assert headers

    r = await client.post(
        "/api/v1/links/client-invite",
        headers=headers,
    )
    assert r.status_code == 200
    token = r.json()["token"]

    r2 = await client.post(
        f"/api/v1/links/redeem/{token}",
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "ignored_self_redeem"


@pytest.mark.asyncio
async def test_specialist_invite_cannot_be_reused(client: AsyncClient):
    """specialist_invite is single-use; second redeem returns 400."""
    await _register(client, "spec@test.com", "password123")
    await _register(client, "client1@test.com", "password123")
    await _register(client, "client2@test.com", "password123")

    spec_headers = await _auth_headers(client, "spec@test.com", "password123")
    c1_headers = await _auth_headers(client, "client1@test.com", "password123")
    c2_headers = await _auth_headers(client, "client2@test.com", "password123")
    assert spec_headers and c1_headers and c2_headers

    r = await client.post(
        "/api/v1/links/specialist-invite",
        headers=spec_headers,
    )
    assert r.status_code == 200
    token = r.json()["token"]

    r1 = await client.post(
        f"/api/v1/links/redeem/{token}",
        headers=c1_headers,
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "linked"

    r2 = await client.post(
        f"/api/v1/links/redeem/{token}",
        headers=c2_headers,
    )
    assert r2.status_code == 400
    assert "already used" in r2.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_duplicate_links_idempotent(client: AsyncClient):
    """Creating duplicate link via multi-use client invite returns already_linked."""
    await _register(client, "inviter@test.com", "password123")
    await _register(client, "redeemer@test.com", "password123")

    inv_headers = await _auth_headers(client, "inviter@test.com", "password123")
    red_headers = await _auth_headers(client, "redeemer@test.com", "password123")
    assert inv_headers and red_headers

    r = await client.post(
        "/api/v1/links/client-invite",
        headers=inv_headers,
        json={"single_use": False},
    )
    assert r.status_code == 200
    token = r.json()["token"]

    r1 = await client.post(
        f"/api/v1/links/redeem/{token}",
        headers=red_headers,
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "linked"

    r2 = await client.post(
        f"/api/v1/links/redeem/{token}",
        headers=red_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_linked"


@pytest.mark.asyncio
async def test_client_exists_without_specialist(client: AsyncClient):
    """Client can register and use endpoints without any links."""
    await _register(client, "standalone@test.com", "password123")
    headers = await _auth_headers(client, "standalone@test.com", "password123")
    assert headers

    # Timeline (empty)
    r = await client.get("/api/v1/entries/timeline", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    # Summary
    r = await client.get("/api/v1/summary", headers=headers)
    assert r.status_code == 200

    # Create task
    r = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"description": "Test task"},
    )
    assert r.status_code == 200

    # List tasks
    r = await client.get("/api/v1/tasks", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
