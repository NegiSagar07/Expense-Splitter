"""initial_schema

Revision ID: bdb80f077b72
Revises:
Create Date: 2026-08-16 08:41:59.160289

Hand-reviewed after autogenerate:
  - Enum values corrected to lowercase (matching Python enum .value)
  - Partial index WHERE clauses use lowercase enum values
  - Partial indexes created after their parent tables (ordering fix)
  - downgrade() drops enum types explicitly
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bdb80f077b72"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Enum type definitions (lowercase values matching Python enum .value)
# ---------------------------------------------------------------------------
member_role = sa.Enum(
    "super_admin", "admin", "member", name="member_role"
)
member_status = sa.Enum("active", "left", name="member_status")
join_request_status = sa.Enum(
    "pending", "approved", "rejected", "expired", name="join_request_status"
)
admin_request_status = sa.Enum(
    "pending", "approved", "rejected", name="admin_request_status"
)
split_type = sa.Enum("equal", "custom", name="split_type")
share_status = sa.Enum(
    "pending", "approved", "rejected", name="share_status"
)


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique user identifier (UUID v4)",
        ),
        sa.Column(
            "name", sa.String(length=255), nullable=False,
            comment="Display name of the user",
        ),
        sa.Column(
            "email", sa.String(length=320), nullable=False,
            comment="Unique email address used for login",
        ),
        sa.Column(
            "password_hash", sa.Text(), nullable=False,
            comment="bcrypt / argon2 hash — never store plaintext",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the account was created",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ── groups ─────────────────────────────────────────────────────────────
    op.create_table(
        "groups",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique group identifier (UUID v4)",
        ),
        sa.Column(
            "name", sa.String(length=255), nullable=False,
            comment="Human-readable group name",
        ),
        sa.Column(
            "created_by", sa.UUID(), nullable=False,
            comment="FK → users.id; the user who originally created this group",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the group was created",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── admin_requests ─────────────────────────────────────────────────────
    op.create_table(
        "admin_requests",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique admin-request identifier",
        ),
        sa.Column(
            "group_id", sa.UUID(), nullable=False,
            comment="FK → groups.id — the group the promotion is requested in",
        ),
        sa.Column(
            "user_id", sa.UUID(), nullable=False,
            comment="FK → users.id — the requesting member",
        ),
        sa.Column(
            "status", admin_request_status, nullable=False,
            comment="pending | approved | rejected",
        ),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the promotion request was submitted",
        ),
        sa.Column(
            "resolved_by", sa.UUID(), nullable=True,
            comment="FK → users.id — admin/super_admin who resolved the request",
        ),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), nullable=True,
            comment="UTC timestamp when the request was resolved",
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_requests_group_id", "admin_requests", ["group_id"], unique=False,
    )
    op.create_index(
        "ix_admin_requests_user_id", "admin_requests", ["user_id"], unique=False,
    )
    # Partial unique index — only one PENDING admin request per (group, user)
    op.create_index(
        "ix_one_pending_admin_request_per_user_group",
        "admin_requests", ["group_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    # ── expenses ───────────────────────────────────────────────────────────
    op.create_table(
        "expenses",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique expense identifier (UUID v4)",
        ),
        sa.Column(
            "group_id", sa.UUID(), nullable=False,
            comment="FK → groups.id — the group this expense belongs to",
        ),
        sa.Column(
            "owner_id", sa.UUID(), nullable=False,
            comment="FK → users.id — the member who logged this expense.",
        ),
        sa.Column(
            "description", sa.Text(), nullable=False,
            comment="Human-readable description of what the expense was for",
        ),
        sa.Column(
            "total_amount", sa.Numeric(precision=12, scale=2), nullable=False,
            comment="Total monetary amount — NUMERIC avoids floating-point errors",
        ),
        sa.Column(
            "split_type", split_type, nullable=False,
            comment="equal = divide evenly; custom = per-participant amounts",
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default="false", nullable=False,
            comment="Soft-delete flag (FR10a).",
        ),
        sa.Column(
            "owner_locked", sa.Boolean(), server_default="false", nullable=False,
            comment="Set True when the owner leaves the group (FR10b).",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the expense was first created",
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp of the last edit",
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_group_id", "expenses", ["group_id"], unique=False)
    op.create_index(
        "ix_expenses_group_is_deleted", "expenses", ["group_id", "is_deleted"],
        unique=False,
    )
    op.create_index("ix_expenses_owner_id", "expenses", ["owner_id"], unique=False)

    # ── group_memberships ──────────────────────────────────────────────────
    op.create_table(
        "group_memberships",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique membership record identifier",
        ),
        sa.Column("group_id", sa.UUID(), nullable=False, comment="FK → groups.id"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="FK → users.id"),
        sa.Column(
            "role", member_role, nullable=False,
            comment="Role within this group: super_admin | admin | member",
        ),
        sa.Column(
            "status", member_status, nullable=False,
            comment="active = current member; left = departed",
        ),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the membership became active",
        ),
        sa.Column(
            "left_at", sa.DateTime(timezone=True), nullable=True,
            comment="UTC timestamp when the user left the group",
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_membership_user"),
    )
    op.create_index(
        "ix_group_memberships_group_id", "group_memberships", ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_group_memberships_user_id", "group_memberships", ["user_id"],
        unique=False,
    )
    # Partial unique index — exactly one active super_admin per group (FR-A1)
    op.create_index(
        "ix_one_super_admin_per_group",
        "group_memberships", ["group_id"],
        unique=True,
        postgresql_where=sa.text("role = 'super_admin' AND status = 'active'"),
    )

    # ── join_requests ──────────────────────────────────────────────────────
    op.create_table(
        "join_requests",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique join-request identifier",
        ),
        sa.Column(
            "group_id", sa.UUID(), nullable=False,
            comment="FK → groups.id — the group the user wants to join",
        ),
        sa.Column(
            "user_id", sa.UUID(), nullable=False,
            comment="FK → users.id — the applicant",
        ),
        sa.Column(
            "status", join_request_status, nullable=False,
            comment="pending | approved | rejected | expired",
        ),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="UTC timestamp when the request was submitted",
        ),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), nullable=True,
            comment="UTC timestamp when the request was resolved",
        ),
        sa.Column(
            "resolved_by", sa.UUID(), nullable=True,
            comment="FK → users.id — admin/super_admin who acted on the request",
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_join_requests_group_id", "join_requests", ["group_id"], unique=False,
    )
    op.create_index(
        "ix_join_requests_status_requested_at", "join_requests",
        ["status", "requested_at"], unique=False,
    )
    op.create_index(
        "ix_join_requests_user_id", "join_requests", ["user_id"], unique=False,
    )
    # Partial unique index — one pending join request per (user, group) at a time
    op.create_index(
        "ix_one_pending_join_request_per_user_group",
        "join_requests", ["group_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    # ── expense_shares ─────────────────────────────────────────────────────
    op.create_table(
        "expense_shares",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            comment="Unique expense-share identifier",
        ),
        sa.Column("expense_id", sa.UUID(), nullable=False, comment="FK → expenses.id"),
        sa.Column(
            "user_id", sa.UUID(), nullable=False,
            comment="FK → users.id — the participant",
        ),
        sa.Column(
            "amount", sa.Numeric(precision=12, scale=2), nullable=False,
            comment="This participant's monetary share. NUMERIC(12,2).",
        ),
        sa.Column(
            "status", share_status, nullable=False,
            comment="pending | approved | rejected",
        ),
        sa.Column(
            "responded_at", sa.DateTime(timezone=True), nullable=True,
            comment="UTC timestamp when the participant responded",
        ),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expense_id", "user_id", name="uq_expense_share_user"),
    )
    op.create_index(
        "ix_expense_shares_expense_id", "expense_shares", ["expense_id"],
        unique=False,
    )
    op.create_index(
        "ix_expense_shares_status", "expense_shares", ["status"], unique=False,
    )
    op.create_index(
        "ix_expense_shares_user_id", "expense_shares", ["user_id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expense_shares_user_id", table_name="expense_shares")
    op.drop_index("ix_expense_shares_status", table_name="expense_shares")
    op.drop_index("ix_expense_shares_expense_id", table_name="expense_shares")
    op.drop_table("expense_shares")

    op.drop_index(
        "ix_one_pending_join_request_per_user_group",
        table_name="join_requests",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index("ix_join_requests_user_id", table_name="join_requests")
    op.drop_index("ix_join_requests_status_requested_at", table_name="join_requests")
    op.drop_index("ix_join_requests_group_id", table_name="join_requests")
    op.drop_table("join_requests")

    op.drop_index(
        "ix_one_super_admin_per_group",
        table_name="group_memberships",
        postgresql_where=sa.text("role = 'super_admin' AND status = 'active'"),
    )
    op.drop_index("ix_group_memberships_user_id", table_name="group_memberships")
    op.drop_index("ix_group_memberships_group_id", table_name="group_memberships")
    op.drop_table("group_memberships")

    op.drop_index("ix_expenses_owner_id", table_name="expenses")
    op.drop_index("ix_expenses_group_is_deleted", table_name="expenses")
    op.drop_index("ix_expenses_group_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index(
        "ix_one_pending_admin_request_per_user_group",
        table_name="admin_requests",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index("ix_admin_requests_user_id", table_name="admin_requests")
    op.drop_index("ix_admin_requests_group_id", table_name="admin_requests")
    op.drop_table("admin_requests")

    op.drop_table("groups")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enum types explicitly
    member_role.drop(op.get_bind(), checkfirst=True)
    member_status.drop(op.get_bind(), checkfirst=True)
    join_request_status.drop(op.get_bind(), checkfirst=True)
    admin_request_status.drop(op.get_bind(), checkfirst=True)
    split_type.drop(op.get_bind(), checkfirst=True)
    share_status.drop(op.get_bind(), checkfirst=True)
