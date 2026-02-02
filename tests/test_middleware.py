"""
Unit tests for core/middleware.py

Tests cover security headers, rate limiting, and CORS origin configuration.
"""
import os
import pytest


class TestSecurityHeaders:
    @pytest.mark.anyio
    async def test_security_headers_present(self, client):
        """Responses should include all mandatory security headers."""
        response = await client.get("/health")
        assert response.status_code == 200

        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-xss-protection") == "1; mode=block"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers.get("permissions-policy", "")

    @pytest.mark.anyio
    async def test_request_id_header(self, client):
        """Responses should include an X-Request-ID header."""
        response = await client.get("/api/v1/test")
        assert response.status_code == 200
        assert "x-request-id" in response.headers

    @pytest.mark.anyio
    async def test_response_time_header(self, client):
        """Responses should include an X-Response-Time header."""
        response = await client.get("/api/v1/test")
        assert response.status_code == 200
        assert "x-response-time" in response.headers


class TestRateLimit:
    @pytest.mark.anyio
    async def test_rate_limit(self, client):
        """Exceeding the rate limit should return 429 Too Many Requests.

        The test app fixture configures RateLimitMiddleware with requests_per_minute=5.
        We send 6 requests to a non-health endpoint; the 6th should be rejected.
        """
        for i in range(5):
            resp = await client.get("/api/v1/test")
            assert resp.status_code == 200, f"Request {i+1} failed unexpectedly"

        # The 6th request should be rate-limited
        resp = await client.get("/api/v1/test")
        assert resp.status_code == 429
        data = resp.json()
        assert "Rate limit" in data.get("detail", "")

    @pytest.mark.anyio
    async def test_rate_limit_headers(self, client):
        """Successful responses should include rate limit headers."""
        resp = await client.get("/api/v1/test")
        assert resp.status_code == 200
        assert "x-ratelimit-limit" in resp.headers
        assert "x-ratelimit-remaining" in resp.headers

    @pytest.mark.anyio
    async def test_health_bypasses_rate_limit(self, client):
        """The /health endpoint should not be subject to rate limiting."""
        # Exhaust the rate limit first
        for _ in range(6):
            await client.get("/api/v1/test")

        # /health should still work
        resp = await client.get("/health")
        assert resp.status_code == 200


class TestCorsOrigins:
    def test_cors_origins(self):
        """get_cors_origins should return the default development origins."""
        # Clear CORS_ORIGINS to force defaults
        old = os.environ.pop("CORS_ORIGINS", None)
        try:
            from core.middleware import get_cors_origins
            origins = get_cors_origins()
            assert isinstance(origins, list)
            assert len(origins) > 0
            assert "http://localhost:5173" in origins
        finally:
            if old is not None:
                os.environ["CORS_ORIGINS"] = old

    def test_cors_origins_from_env(self):
        """get_cors_origins should parse CORS_ORIGINS from the environment."""
        old = os.environ.get("CORS_ORIGINS")
        os.environ["CORS_ORIGINS"] = "https://example.com, https://app.example.com"
        try:
            from core.middleware import get_cors_origins
            origins = get_cors_origins()
            assert "https://example.com" in origins
            assert "https://app.example.com" in origins
        finally:
            if old is not None:
                os.environ["CORS_ORIGINS"] = old
            else:
                os.environ.pop("CORS_ORIGINS", None)
