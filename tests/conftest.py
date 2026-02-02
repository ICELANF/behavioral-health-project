"""
Pytest fixtures for the behavioral health platform test suite.
"""
import os
import sys
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set test environment variables before any application imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_RPM", "120")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.models import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine for the entire test session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    """Provide a transactional database session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def app():
    """Create a minimal FastAPI test application with middleware configured."""
    from fastapi import FastAPI

    test_app = FastAPI(title="Test App")

    @test_app.get("/health")
    async def health():
        return {"status": "online", "version": "test"}

    @test_app.get("/api/v1/test")
    async def test_endpoint():
        return {"message": "ok"}

    # Apply production middleware so we can test security headers, rate limiting, etc.
    from core.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, RequestLoggingMiddleware, setup_cors

    setup_cors(test_app)
    test_app.add_middleware(SecurityHeadersMiddleware)
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(RateLimitMiddleware, requests_per_minute=5)

    return test_app


@pytest.fixture()
async def client(app):
    """Provide an async HTTP test client bound to the test app."""
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
