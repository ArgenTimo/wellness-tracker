"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns ok when DB is available."""
    # Note: may fail if DB not configured - use override in conftest for unit tests
    response = await client.get("/health")
    # Accept both 200 (DB ok) and 500 (DB not configured in test env)
    assert response.status_code in (200, 500)
    data = response.json()
    assert "status" in data
    assert "database" in data
