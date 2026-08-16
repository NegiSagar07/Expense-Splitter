"""
app/services/auth_service.py
-----------------------------
Business logic for user registration and authentication.
No HTTP concerns here — raises ValueError for domain errors,
which the endpoint layer converts to HTTPException.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User


async def register_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
) -> User:
    """
    Create a new user account.

    Raises:
        ValueError: if the email is already registered.
    """
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()  # assign UUID without committing
    return user


async def authenticate_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> str:
    """
    Verify credentials and return a JWT access token.

    Raises:
        ValueError: if credentials are invalid.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")

    return create_access_token(subject=str(user.id))
