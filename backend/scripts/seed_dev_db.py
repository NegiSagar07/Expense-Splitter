"""
scripts/seed_dev_db.py
-----------------------
Development seed script — populates the DB with realistic test data.

Run from the project root (with .venv active or inside the container):
    python -m scripts.seed_dev_db

Or inside Docker:
    docker compose exec backend python -m scripts.seed_dev_db

What it creates:
  - 4 users  (alice, bob, charlie, diana)
  - 1 group  "Weekend Trip"
    - alice   → super_admin
    - bob     → admin
    - charlie → member
    - diana   → member  (pending join request — not yet approved)
  - 3 expenses
    - alice paid dinner  ₹1200  equal split (alice, bob, charlie)
    - bob   paid petrol  ₹900   custom split (alice ₹300, bob ₹300, charlie ₹300)
    - charlie paid snacks ₹600  equal split (charlie, diana) — diana hasn't approved yet
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Ensure the backend app package is importable
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.models import (
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

settings = get_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------


USERS = [
    {"name": "Alice Sharma",   "email": "alice@example.com",   "password": "password123"},
    {"name": "Bob Verma",      "email": "bob@example.com",     "password": "password123"},
    {"name": "Charlie Singh",  "email": "charlie@example.com", "password": "password123"},
    {"name": "Diana Mehta",    "email": "diana@example.com",   "password": "password123"},
]


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed(session: AsyncSession) -> None:
    print("🌱  Seeding development database...")

    # ── Users ──────────────────────────────────────────────────────────────
    users: dict[str, User] = {}
    for u in USERS:
        user = User(
            name=u["name"],
            email=u["email"],
            password_hash=hash_password(u["password"]),
        )
        session.add(user)
        users[u["email"].split("@")[0]] = user  # key: alice, bob, etc.

    await session.flush()  # get UUIDs assigned
    print(f"  ✓ Created {len(users)} users")

    # ── Group ──────────────────────────────────────────────────────────────
    group = Group(name="Weekend Trip", created_by=users["alice"].id)
    session.add(group)
    await session.flush()
    print(f"  ✓ Created group: '{group.name}'")

    # ── Memberships ────────────────────────────────────────────────────────
    memberships = [
        GroupMembership(
            group_id=group.id, user_id=users["alice"].id,
            role=MemberRole.SUPER_ADMIN, status=MemberStatus.ACTIVE,
        ),
        GroupMembership(
            group_id=group.id, user_id=users["bob"].id,
            role=MemberRole.ADMIN, status=MemberStatus.ACTIVE,
        ),
        GroupMembership(
            group_id=group.id, user_id=users["charlie"].id,
            role=MemberRole.MEMBER, status=MemberStatus.ACTIVE,
        ),
    ]
    session.add_all(memberships)

    # Diana has a pending join request (not yet a member)
    join_req = JoinRequest(
        group_id=group.id,
        user_id=users["diana"].id,
        status=JoinRequestStatus.PENDING,
    )
    session.add(join_req)
    await session.flush()
    print("  ✓ Created memberships (alice=super_admin, bob=admin, charlie=member)")
    print("  ✓ Created pending join request for diana")

    # ── Expenses ───────────────────────────────────────────────────────────

    # Expense 1: Alice paid dinner — equal split (alice, bob, charlie)
    dinner = Expense(
        group_id=group.id,
        owner_id=users["alice"].id,
        description="Dinner at Spice Garden",
        total_amount=Decimal("1200.00"),
        split_type=SplitType.EQUAL,
    )
    session.add(dinner)
    await session.flush()

    per_person = Decimal("400.00")
    dinner_shares = [
        ExpenseShare(expense_id=dinner.id, user_id=users["alice"].id,
                     amount=per_person, status=ShareStatus.APPROVED,
                     responded_at=now_utc()),
        ExpenseShare(expense_id=dinner.id, user_id=users["bob"].id,
                     amount=per_person, status=ShareStatus.APPROVED,
                     responded_at=now_utc()),
        ExpenseShare(expense_id=dinner.id, user_id=users["charlie"].id,
                     amount=per_person, status=ShareStatus.PENDING),
    ]
    session.add_all(dinner_shares)
    print("  ✓ Expense 1: Dinner ₹1200 (equal split) — charlie pending approval")

    # Expense 2: Bob paid petrol — custom split
    petrol = Expense(
        group_id=group.id,
        owner_id=users["bob"].id,
        description="Petrol for road trip",
        total_amount=Decimal("900.00"),
        split_type=SplitType.CUSTOM,
    )
    session.add(petrol)
    await session.flush()

    petrol_shares = [
        ExpenseShare(expense_id=petrol.id, user_id=users["alice"].id,
                     amount=Decimal("300.00"), status=ShareStatus.APPROVED,
                     responded_at=now_utc()),
        ExpenseShare(expense_id=petrol.id, user_id=users["bob"].id,
                     amount=Decimal("300.00"), status=ShareStatus.APPROVED,
                     responded_at=now_utc()),
        ExpenseShare(expense_id=petrol.id, user_id=users["charlie"].id,
                     amount=Decimal("300.00"), status=ShareStatus.APPROVED,
                     responded_at=now_utc()),
    ]
    session.add_all(petrol_shares)
    print("  ✓ Expense 2: Petrol ₹900 (custom split) — all approved")

    # Expense 3: Charlie paid snacks — soft-deleted example
    snacks = Expense(
        group_id=group.id,
        owner_id=users["charlie"].id,
        description="Snacks (duplicate entry — deleted)",
        total_amount=Decimal("200.00"),
        split_type=SplitType.EQUAL,
        is_deleted=True,
    )
    session.add(snacks)
    await session.flush()

    snacks_shares = [
        ExpenseShare(expense_id=snacks.id, user_id=users["charlie"].id,
                     amount=Decimal("100.00"), status=ShareStatus.APPROVED),
        ExpenseShare(expense_id=snacks.id, user_id=users["alice"].id,
                     amount=Decimal("100.00"), status=ShareStatus.APPROVED),
    ]
    session.add_all(snacks_shares)
    print("  ✓ Expense 3: Snacks ₹200 — soft-deleted (history demo)")

    await session.commit()
    print()
    print("✅  Seed complete!")
    print()
    print("  Login credentials (all passwords: password123)")
    print("  ┌──────────────────────────────────────────┐")
    for u in USERS:
        print(f"  │  {u['email']:<35}│")
    print("  └──────────────────────────────────────────┘")
    print()
    print("  Expected balance (approved shares only, excl. deleted):")
    print("  • charlie owes alice  ₹400  (dinner not yet approved → PENDING)")
    print("  • alice   owes bob    ₹300  (petrol approved)")
    print("  • charlie owes bob    ₹300  (petrol approved)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
