"""
app/api/v1/endpoints/auth.py
-----------------------------
Authentication endpoints: register, login, and current-user profile.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.exceptions import bad_request, conflict
from app.db.session import get_db
from app.models.models import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserRead
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Create a new user account.
    - Email must be unique across the system.
    - Password is hashed server-side; plaintext is never stored.
    """
    try:
        user = await auth_service.register_user(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
        await db.commit()
        await db.refresh(user)
        return user
    except ValueError as exc:
        raise conflict(str(exc))


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate with email + password.
    Returns a short-lived JWT access token (default: 30 min).
    """
    try:
        token = await auth_service.authenticate_user(
            db,
            email=payload.email,
            password=payload.password,
        )
        return Token(access_token=token)
    except ValueError as exc:
        raise bad_request(str(exc))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
