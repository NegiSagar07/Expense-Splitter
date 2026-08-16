"""
app/models/models.py
--------------------
SQLAlchemy 2.0 ORM models for the Expense Splitter application.

Design decisions:
  - Uses mapped_column() (SQLAlchemy 2.0 style) — no SQLModel.
  - All primary keys are UUID v4 — no sequential integer IDs exposed
    to the outside world (prevents enumeration attacks).
  - All timestamps are stored in UTC with timezone awareness (TIMESTAMP
    WITH TIME ZONE / timestamptz in PostgreSQL).
  - Money columns use NUMERIC(12, 2) — never float/double (avoids
    floating-point rounding errors for currency).
  - Enums are defined as Python enums and mapped to PostgreSQL native
    enum types for maximum data integrity.
  - Soft-deletes (is_deleted flag) on Expense — rows are never physically
    removed so the permanent-history requirement (FR6, FR10a) is met.
  - owner_locked on Expense implements FR10b: once an expense owner
    leaves the group, their expenses become read-only.
  - The partial unique index enforcing exactly one super_admin per group
    (FR-A1) is defined here via __table_args__ and Index with postgresql_where.
  - Relationships use lazy="selectin" so async SQLAlchemy sessions do not
    attempt implicit lazy-loads (which are not supported in async mode).

References:
  - Specs.md §6 (roles), §8.1–8.4 (functional requirements)
  - Design.md §2.2 (table definitions), §2.3 (key constraints)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """
    Shared declarative base.
    All models inherit from this.  Metadata is shared so Alembic and
    create_all() both see every table.
    """


# ---------------------------------------------------------------------------
# Enum types
# ---------------------------------------------------------------------------


class MemberRole(str, enum.Enum):
    """Role a user holds within a specific group (Design.md §2.2 group_memberships)."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MEMBER = "member"


class MemberStatus(str, enum.Enum):
    """Whether the user is still in the group or has left (FR6)."""

    ACTIVE = "active"
    LEFT = "left"


class JoinRequestStatus(str, enum.Enum):
    """Life-cycle states of a join request (FR3, FR4, FR4a)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"  # auto-set after 7 days (FR4a)


class AdminRequestStatus(str, enum.Enum):
    """Life-cycle states of a member's request to become an admin (FR-A2)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SplitType(str, enum.Enum):
    """How the expense total is divided among participants (FR9)."""

    EQUAL = "equal"
    CUSTOM = "custom"


class ShareStatus(str, enum.Enum):
    """Whether a participant has responded to their expense share (FR12–FR14)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Helper: default UUID factory
# ---------------------------------------------------------------------------


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Model: User
# ---------------------------------------------------------------------------


class User(Base):
    """
    Represents an application account.

    Design.md §2.2 — `users` table.
    Passwords are NEVER stored here in plaintext; only the bcrypt/argon2
    hash produced by the auth service is persisted.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique user identifier (UUID v4)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the user",
    )
    email: Mapped[str] = mapped_column(
        String(320),          # RFC 5321 max email length
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address used for login",
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="bcrypt / argon2 hash — never store plaintext",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the account was created",
    )

    # ------------------------------------------------------------------
    # Relationships (back-references for convenience queries)
    # ------------------------------------------------------------------
    memberships: Mapped[list[GroupMembership]] = relationship(
        "GroupMembership",
        back_populates="user",
        lazy="selectin",
    )
    created_groups: Mapped[list[Group]] = relationship(
        "Group",
        back_populates="creator",
        foreign_keys="Group.created_by",
        lazy="selectin",
    )
    owned_expenses: Mapped[list[Expense]] = relationship(
        "Expense",
        back_populates="owner",
        foreign_keys="Expense.owner_id",
        lazy="selectin",
    )
    expense_shares: Mapped[list[ExpenseShare]] = relationship(
        "ExpenseShare",
        back_populates="user",
        lazy="selectin",
    )
    join_requests: Mapped[list[JoinRequest]] = relationship(
        "JoinRequest",
        back_populates="user",
        foreign_keys="JoinRequest.user_id",
        lazy="selectin",
    )
    admin_requests: Mapped[list[AdminRequest]] = relationship(
        "AdminRequest",
        back_populates="user",
        foreign_keys="AdminRequest.user_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ---------------------------------------------------------------------------
# Model: Group
# ---------------------------------------------------------------------------


class Group(Base):
    """
    A named group that members share expenses within.

    Design.md §2.2 — `groups` table.
    The creator automatically becomes the Super Admin (FR2); that membership
    row is created in the service layer when a group is first saved.
    """

    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique group identifier (UUID v4)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable group name",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id; the user who originally created this group",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the group was created",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    creator: Mapped[User] = relationship(
        "User",
        back_populates="created_groups",
        foreign_keys=[created_by],
        lazy="selectin",
    )
    memberships: Mapped[list[GroupMembership]] = relationship(
        "GroupMembership",
        back_populates="group",
        lazy="selectin",
    )
    expenses: Mapped[list[Expense]] = relationship(
        "Expense",
        back_populates="group",
        lazy="selectin",
    )
    join_requests: Mapped[list[JoinRequest]] = relationship(
        "JoinRequest",
        back_populates="group",
        lazy="selectin",
    )
    admin_requests: Mapped[list[AdminRequest]] = relationship(
        "AdminRequest",
        back_populates="group",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Group id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Model: GroupMembership
# ---------------------------------------------------------------------------


class GroupMembership(Base):
    """
    Join table that records a user's membership and role within a group.

    Design.md §2.2 — `group_memberships` table.

    Key constraints (Design.md §2.3):
      - Exactly one SUPER_ADMIN per group — enforced by a partial unique
        index: UNIQUE (group_id) WHERE role = 'super_admin' AND status = 'active'.
        Defined in __table_args__ below.
      - A user can appear in this table even after leaving (status='left')
        so their expense history remains linked (FR6).
    """

    __tablename__ = "group_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique membership record identifier",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → groups.id",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → users.id",
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MemberRole.MEMBER,
        comment="Role within this group: super_admin | admin | member",
    )
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus, name="member_status", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MemberStatus.ACTIVE,
        comment="active = current member; left = departed (history preserved, FR6)",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the membership became active",
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="UTC timestamp when the user left the group (NULL if still active)",
    )

    # ------------------------------------------------------------------
    # Table-level constraints and indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Every (group, user) pair may only have ONE membership row.
        # (A user who re-joins would get a new row after the old one is
        #  set to status='left', but we keep it simple for v1.)
        UniqueConstraint("group_id", "user_id", name="uq_group_membership_user"),
        # Partial unique index: at most one ACTIVE super_admin per group.
        # This is a PostgreSQL-specific construct that enforces FR-A1.
        Index(
            "ix_one_super_admin_per_group",
            "group_id",
            unique=True,
            postgresql_where=(
                "role = 'super_admin' AND status = 'active'"
            ),
        ),
        # General lookup index
        Index("ix_group_memberships_group_id", "group_id"),
        Index("ix_group_memberships_user_id", "user_id"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    group: Mapped[Group] = relationship(
        "Group",
        back_populates="memberships",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="memberships",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<GroupMembership group={self.group_id} "
            f"user={self.user_id} role={self.role} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Model: JoinRequest
# ---------------------------------------------------------------------------


class JoinRequest(Base):
    """
    Records a user's request to join a group, pending admin approval.

    Design.md §2.2 — `join_requests` table.

    Life-cycle (FR3, FR4, FR4a):
      pending → approved  (admin/super_admin acts)
      pending → rejected  (admin/super_admin acts)
      pending → expired   (7-day background sweep — FR4a; row kept for audit)
    """

    __tablename__ = "join_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique join-request identifier",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → groups.id — the group the user wants to join",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → users.id — the applicant",
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        Enum(JoinRequestStatus, name="join_request_status", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=JoinRequestStatus.PENDING,
        comment="pending | approved | rejected | expired",
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the request was submitted",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="UTC timestamp when the request was resolved (NULL if still pending)",
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        comment="FK → users.id — admin/super_admin who acted on the request",
    )

    __table_args__ = (
        # A user should have at most one pending request per group at a time.
        Index(
            "ix_one_pending_join_request_per_user_group",
            "group_id",
            "user_id",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
        Index("ix_join_requests_group_id", "group_id"),
        Index("ix_join_requests_user_id", "user_id"),
        # Speed up the 7-day expiry sweep (FR4a)
        Index("ix_join_requests_status_requested_at", "status", "requested_at"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    group: Mapped[Group] = relationship(
        "Group",
        back_populates="join_requests",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="join_requests",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    resolver: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<JoinRequest id={self.id} group={self.group_id} "
            f"user={self.user_id} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Model: AdminRequest
# ---------------------------------------------------------------------------


class AdminRequest(Base):
    """
    Records a member's request to be promoted to Admin within a group.

    Design.md §2.2 — `admin_requests` table.
    FR-A2: a member can request promotion; an Admin/Super Admin approves.
    Direct promotion (without a request) is handled in the service layer.
    """

    __tablename__ = "admin_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique admin-request identifier",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → groups.id — the group the promotion is requested in",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → users.id — the requesting member",
    )
    status: Mapped[AdminRequestStatus] = mapped_column(
        Enum(AdminRequestStatus, name="admin_request_status", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=AdminRequestStatus.PENDING,
        comment="pending | approved | rejected",
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the promotion request was submitted",
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        comment="FK → users.id — admin/super_admin who resolved the request",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="UTC timestamp when the request was resolved",
    )

    __table_args__ = (
        # A member should only have one pending admin request per group.
        Index(
            "ix_one_pending_admin_request_per_user_group",
            "group_id",
            "user_id",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
        Index("ix_admin_requests_group_id", "group_id"),
        Index("ix_admin_requests_user_id", "user_id"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    group: Mapped[Group] = relationship(
        "Group",
        back_populates="admin_requests",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="admin_requests",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    resolver: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AdminRequest id={self.id} group={self.group_id} "
            f"user={self.user_id} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Model: Expense
# ---------------------------------------------------------------------------


class Expense(Base):
    """
    An expense logged by a group member (the owner).

    Design.md §2.2 — `expenses` table.

    Key behaviours:
      - is_deleted (FR10a): soft-delete flag — the row is NEVER physically
        removed; it is marked deleted and stays in history.
      - owner_locked (FR10b): set to True by the service layer when the
        expense owner's GroupMembership.status transitions to 'left'. After
        that, edit/delete endpoints must reject with 403.
      - Balance calculation (FR15) only sums shares where the parent expense
        has is_deleted=False and the share status='approved'.
    """

    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique expense identifier (UUID v4)",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → groups.id — the group this expense belongs to",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment=(
            "FK → users.id — the member who logged this expense. "
            "Only they can edit/delete it (FR10)."
        ),
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description of what the expense was for",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment=(
            "Total monetary amount — uses NUMERIC to avoid floating-point "
            "rounding errors (Design.md §2.2)"
        ),
    )
    split_type: Mapped[SplitType] = mapped_column(
        Enum(SplitType, name="split_type", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        comment="equal = divide evenly; custom = per-participant amounts (FR9)",
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment=(
            "Soft-delete flag (FR10a). When True the expense is hidden from "
            "active views but NEVER erased — permanent history is preserved."
        ),
    )
    owner_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment=(
            "Set True when the owner leaves the group (FR10b). "
            "Prevents any further edits/deletes by the original owner."
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the expense was first created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="UTC timestamp of the last edit (auto-updated on any change)",
    )

    __table_args__ = (
        Index("ix_expenses_group_id", "group_id"),
        Index("ix_expenses_owner_id", "owner_id"),
        # Speed up balance queries that filter on is_deleted + group_id
        Index("ix_expenses_group_is_deleted", "group_id", "is_deleted"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    group: Mapped[Group] = relationship(
        "Group",
        back_populates="expenses",
        lazy="selectin",
    )
    owner: Mapped[User] = relationship(
        "User",
        back_populates="owned_expenses",
        foreign_keys=[owner_id],
        lazy="selectin",
    )
    shares: Mapped[list[ExpenseShare]] = relationship(
        "ExpenseShare",
        back_populates="expense",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Expense id={self.id} group={self.group_id} "
            f"amount={self.total_amount} deleted={self.is_deleted}>"
        )


# ---------------------------------------------------------------------------
# Model: ExpenseShare
# ---------------------------------------------------------------------------


class ExpenseShare(Base):
    """
    One participant's share of an expense, including their approval status.

    Design.md §2.2 — `expense_shares` table.

    FR8:  Participants are explicitly selected — not everyone in the group.
    FR12: The participant must approve their share before it counts.
    FR13: Only 'approved' shares contribute to balance totals.
    FR14: A 'rejected' status is visible to the expense owner.

    Balance formula (FR15):
        For each pair (payer, debtor) in a group:
            net = SUM(amount) WHERE
                    expense.group_id = <group>
                    AND expense.is_deleted = false
                    AND share.status = 'approved'
                    AND share.user_id = debtor          ← owes money
                    AND expense.owner_id = payer        ← paid
        Then net out A-owes-B vs B-owes-A (FR16).
    """

    __tablename__ = "expense_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_new_uuid,
        comment="Unique expense-share identifier",
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → expenses.id",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id — the participant whose share this row represents",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment=(
            "This participant's monetary share. "
            "NUMERIC(12,2) to avoid floating-point errors."
        ),
    )
    status: Mapped[ShareStatus] = mapped_column(
        Enum(ShareStatus, name="share_status", create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ShareStatus.PENDING,
        comment="pending | approved | rejected (FR12–FR14)",
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="UTC timestamp when the participant approved or rejected their share",
    )

    __table_args__ = (
        # Each user appears at most once per expense
        UniqueConstraint("expense_id", "user_id", name="uq_expense_share_user"),
        Index("ix_expense_shares_expense_id", "expense_id"),
        Index("ix_expense_shares_user_id", "user_id"),
        # Balance calculation query index (FR15)
        Index("ix_expense_shares_status", "status"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    expense: Mapped[Expense] = relationship(
        "Expense",
        back_populates="shares",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="expense_shares",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ExpenseShare expense={self.expense_id} "
            f"user={self.user_id} amount={self.amount} status={self.status}>"
        )
