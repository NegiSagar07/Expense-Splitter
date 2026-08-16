"""
tests/conftest.py
------------------
Pytest fixtures for async integration and unit testing.
Uses dependency overrides so FastAPI endpoints use the test session.
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.session import AsyncSessionLocal, engine, get_db
from app.main import app
from app.models.models import User


@pytest_asyncio.fixture(scope="function", autouse=True)
async def dispose_engine_after_test():
    """Dispose connection pool before/after tests so asyncpg connections don't cross event loops."""
    await engine.dispose()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an AsyncSession and overrides get_db for FastAPI test client."""
    async with AsyncSessionLocal() as session:
        # Override FastAPI get_db dependency so endpoint requests use this exact session
        async def _override_get_db():
            yield session

        app.dependency_overrides[get_db] = _override_get_db
        try:
            yield session
        finally:
            app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yields an httpx.AsyncClient bound to the FastAPI ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def create_user(db_session: AsyncSession):
    """Factory fixture to create users on demand."""
    async def _create(name: str = "Test User", email: str | None = None, password: str = "password123") -> User:
        if email is None:
            email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    yield _create


@pytest_asyncio.fixture
async def auth_headers():
    """Helper to return authorization headers for a given user object."""
    def _headers(user: User) -> dict[str, str]:
        token = create_access_token(subject=str(user.id))
        return {"Authorization": f"Bearer {token}"}
    return _headers
