"""
Unit tests for the health endpoint.

Tests verify that the /health route returns the expected status and structure.
"""
import pytest


class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_health_endpoint(self, client):
        """GET /health should return 200 with status=online."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"

    @pytest.mark.anyio
    async def test_basic_health_check(self, client):
        """GET /health response should include a version field."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "status" in data
