"""Root and docs endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Root returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Wellness Tracker API"
    assert "docs" in data
    assert "api" in data
