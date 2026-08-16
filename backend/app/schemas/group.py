"""
app/schemas/group.py
---------------------
Pydantic v2 schemas for groups, memberships, and the leave-group action.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import MemberRole, MemberStatus
from app.schemas.user import UserRead


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


class GroupCreate(BaseModel):
    """Payload for POST /groups."""

    name: str = Field(..., min_length=1, max_length=255)


class GroupRead(BaseModel):
    """Flat group representation (no member list)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------


class MembershipRead(BaseModel):
    """A user's membership record within a group."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    role: MemberRole
    status: MemberStatus
    joined_at: datetime
    left_at: datetime | None = None
    user: UserRead | None = None  # populated when joining eager-loaded data


class GroupDetailRead(BaseModel):
    """Group with its full active member list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime
    members: list[MembershipRead] = []


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


class LeaveGroupRequest(BaseModel):
    """
    Body for POST /groups/{id}/leave.
    Super Admin MUST supply successor_id (FR-A6).
    Regular admins and members leave freely — field is ignored.
    """

    successor_id: uuid.UUID | None = None


class PromoteRequest(BaseModel):
    """Body is empty — target user_id is in the URL path."""

    pass
