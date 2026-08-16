"""
app/models/__init__.py
----------------------
Re-exports all ORM models so Alembic's env.py can import Base and discover
all tables by simply doing:

    from app.models import Base
"""

from app.models.models import (
    AdminRequest,
    AdminRequestStatus,
    Base,
    Expense,
    ExpenseShare,
    Group,
    GroupMembership,
    JoinRequest,
    JoinRequestStatus,
    MemberRole,
    MemberStatus,
    ShareStatus,
    SplitType,
    User,
)

__all__ = [
    "Base",
    "User",
    "Group",
    "GroupMembership",
    "JoinRequest",
    "AdminRequest",
    "Expense",
    "ExpenseShare",
    # enums
    "MemberRole",
    "MemberStatus",
    "JoinRequestStatus",
    "AdminRequestStatus",
    "SplitType",
    "ShareStatus",
]
