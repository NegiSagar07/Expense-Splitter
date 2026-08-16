"""
app/schemas/request.py
-----------------------
Pydantic v2 schemas for join requests and admin-promotion requests.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.models import AdminRequestStatus, JoinRequestStatus


class JoinRequestRead(BaseModel):
    """Read representation of a group join request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    status: JoinRequestStatus
    requested_at: datetime
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None


class AdminRequestRead(BaseModel):
    """Read representation of an admin-promotion request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    status: AdminRequestStatus
    requested_at: datetime
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
