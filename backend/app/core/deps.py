"""
app/core/deps.py
-----------------
FastAPI dependency functions for authentication and group-level authorization.

Dependency hierarchy:
    get_db                      → yields AsyncSession
    get_current_user            → decodes JWT, returns User
    get_active_membership       → verifies caller is an active group member,
                                  returns (User, GroupMembership)

Role checks are done inline in endpoints using the returned membership.role,
keeping each endpoint's intent explicit rather than hidden in a decorator.
"""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import forbidden, not_found, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.models import Group, GroupMembership, MemberRole, MemberStatus, User

settings = get_settings()

# Tells Swagger UI where to get a token for "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT Bearer token and load the corresponding User from the DB.
    Raises 401 if the token is invalid, expired, or the user no longer exists.
    """
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise unauthorized()
    except JWTError:
        raise unauthorized()

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise unauthorized("User account not found.")
    return user


# ---------------------------------------------------------------------------
# Group membership checks
# ---------------------------------------------------------------------------


async def get_active_membership(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, GroupMembership]:
    """
    Verify the current user is an ACTIVE member of the given group.

    Returns (user, membership) so the endpoint can inspect the role.
    Raises:
        404 — group does not exist
        403 — caller is not an active member of this group
    """
    # Verify group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    if group_result.scalar_one_or_none() is None:
        raise not_found("Group")

    result = await db.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MemberStatus.ACTIVE,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise forbidden("You are not an active member of this group.")
    return current_user, membership


# ---------------------------------------------------------------------------
# Role assertion helpers (called inside endpoints, not used as Depends)
# ---------------------------------------------------------------------------


def assert_admin(membership: GroupMembership) -> None:
    """Raise 403 if the caller is not at least an Admin."""
    if membership.role not in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise forbidden("Admin or Super Admin role required.")


def assert_super_admin(membership: GroupMembership) -> None:
    """Raise 403 if the caller is not the Super Admin."""
    if membership.role != MemberRole.SUPER_ADMIN:
        raise forbidden("Super Admin role required.")
