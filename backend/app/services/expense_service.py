"""
app/services/expense_service.py
--------------------------------
Business logic for expenses and expense shares.

Spec & Functional Requirements enforced:
  - FR9: Equal and Custom split calculation.
  - Remainder handling on EQUAL split: Pennies/paise divided cleanly so sum(shares) == total_amount exactly.
  - FR12-FR14: Expense owner's share is automatically APPROVED. Other participants start as PENDING.
  - Participant can respond (approve/reject) to their share.
  - FR10: Only owner can edit or soft-delete an expense.
  - FR10a: Soft delete (is_deleted=True) — records are preserved permanently in DB history.
  - FR10b: Owner lock (owner_locked=True) — if owner left group, edit/delete is blocked.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import bad_request, forbidden, not_found
from app.models.models import (
    Expense,
    ExpenseShare,
    GroupMembership,
    MemberStatus,
    ShareStatus,
    SplitType,
    User,
)
from app.schemas.expense import CustomShareInput, ExpenseCreate, ExpenseUpdate


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _compute_equal_shares(
    total_amount: Decimal, participant_ids: list[uuid.UUID]
) -> list[tuple[uuid.UUID, Decimal]]:
    """
    Divide total_amount evenly among participant_ids.
    Any fraction/penny remainder is distributed 0.01 at a time to participants
    so that sum(shares) == total_amount exact decimal.
    """
    n = len(participant_ids)
    if n == 0:
        return []

    base_share = (total_amount / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    total_base = base_share * n
    remainder = total_amount - total_base  # in cents/paise (e.g. 0.02)

    shares: list[tuple[uuid.UUID, Decimal]] = []
    # Distribute remainder 0.01 per participant for the first k participants
    cents_left = int((remainder * 100).to_integral_value())

    for idx, pid in enumerate(participant_ids):
        extra = Decimal("0.01") if idx < cents_left else Decimal("0.00")
        shares.append((pid, base_share + extra))

    return shares


async def _validate_participants_active(
    db: AsyncSession, group_id: uuid.UUID, user_ids: list[uuid.UUID]
) -> None:
    """Ensure all target participant user_ids are active members of the group."""
    result = await db.execute(
        select(GroupMembership.user_id).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id.in_(user_ids),
            GroupMembership.status == MemberStatus.ACTIVE,
        )
    )
    active_ids = set(result.scalars().all())
    missing = set(user_ids) - active_ids
    if missing:
        raise bad_request(f"User(s) {missing} are not active members of this group.")


# ---------------------------------------------------------------------------
# Create Expense
# ---------------------------------------------------------------------------


async def create_expense(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    owner: User,
    payload: ExpenseCreate,
) -> Expense:
    """
    Create a new expense and generate shares for participants.
    - Owner's share status is automatically APPROVED.
    - Other participants start as PENDING.
    """
    # 1. Determine participant amounts
    if payload.split_type == SplitType.EQUAL:
        target_user_ids = payload.participant_ids or []
        if owner.id not in target_user_ids:
            # Auto-include owner if omitted, or keep as specified
            pass
        await _validate_participants_active(db, group_id, target_user_ids)
        share_tuples = _compute_equal_shares(payload.total_amount, target_user_ids)
    else:  # CUSTOM
        custom_inputs = payload.custom_shares or []
        target_user_ids = [s.user_id for s in custom_inputs]
        await _validate_participants_active(db, group_id, target_user_ids)
        share_tuples = [(s.user_id, s.amount) for s in custom_inputs]

    # 2. Create Expense record
    expense = Expense(
        group_id=group_id,
        owner_id=owner.id,
        description=payload.description,
        total_amount=payload.total_amount,
        split_type=payload.split_type,
        is_deleted=False,
        owner_locked=False,
    )
    db.add(expense)
    await db.flush()

    # 3. Create ExpenseShare records
    for uid, amt in share_tuples:
        is_owner = uid == owner.id
        share = ExpenseShare(
            expense_id=expense.id,
            user_id=uid,
            amount=amt,
            status=ShareStatus.APPROVED if is_owner else ShareStatus.PENDING,
            responded_at=_now() if is_owner else None,
        )
        db.add(share)

    await db.flush()
    return expense


# ---------------------------------------------------------------------------
# Read Expenses
# ---------------------------------------------------------------------------


async def get_group_expenses(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    include_deleted: bool = False,
) -> list[Expense]:
    """List all expenses for a group with owner and shares eagerly loaded."""
    query = (
        select(Expense)
        .options(
            selectinload(Expense.owner),
            selectinload(Expense.shares).selectinload(ExpenseShare.user),
        )
        .where(Expense.group_id == group_id)
    )
    if not include_deleted:
        query = query.where(Expense.is_deleted == False)  # noqa: E712

    query = query.order_by(Expense.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_expense_by_id(
    db: AsyncSession,
    *,
    expense_id: uuid.UUID,
    group_id: uuid.UUID | None = None,
) -> Expense:
    """Fetch single expense with eagerly loaded owner and shares."""
    query = (
        select(Expense)
        .options(
            selectinload(Expense.owner),
            selectinload(Expense.shares).selectinload(ExpenseShare.user),
        )
        .where(Expense.id == expense_id)
    )
    if group_id is not None:
        query = query.where(Expense.group_id == group_id)

    result = await db.execute(query)
    expense = result.scalar_one_or_none()
    if expense is None:
        raise not_found("Expense")
    return expense


# ---------------------------------------------------------------------------
# Update Expense (FR10, FR10b)
# ---------------------------------------------------------------------------


async def update_expense(
    db: AsyncSession,
    *,
    expense_id: uuid.UUID,
    caller: User,
    payload: ExpenseUpdate,
) -> Expense:
    """
    Update an expense description, amount, or split configuration.

    Rules:
      - Only the owner can edit (FR10).
      - Cannot edit if soft-deleted (is_deleted=True).
      - Cannot edit if owner_locked=True (owner left the group, FR10b).
    """
    expense = await get_expense_by_id(db, expense_id=expense_id)

    if expense.owner_id != caller.id:
        raise forbidden("Only the expense owner can edit this expense (FR10).")

    if expense.is_deleted:
        raise bad_request("Cannot edit a deleted expense.")

    if expense.owner_locked:
        raise forbidden(
            "This expense is locked because the owner left the group (FR10b)."
        )

    # Update basic fields if provided
    if payload.description is not None:
        expense.description = payload.description

    recompute_shares = False
    new_total = payload.total_amount if payload.total_amount is not None else expense.total_amount
    new_split_type = payload.split_type if payload.split_type is not None else expense.split_type

    if (
        payload.total_amount is not None
        or payload.split_type is not None
        or payload.participant_ids is not None
        or payload.custom_shares is not None
    ):
        recompute_shares = True

    if recompute_shares:
        expense.total_amount = new_total
        expense.split_type = new_split_type

        # Determine new share tuples
        if new_split_type == SplitType.EQUAL:
            p_ids = payload.participant_ids
            if p_ids is None:
                # Keep existing participant user_ids if not provided
                p_ids = [s.user_id for s in expense.shares]
            await _validate_participants_active(db, expense.group_id, p_ids)
            share_tuples = _compute_equal_shares(new_total, p_ids)
        else:
            if payload.custom_shares is None:
                raise bad_request("custom_shares is required when switching to CUSTOM split.")
            c_shares = payload.custom_shares
            u_ids = [s.user_id for s in c_shares]
            sum_c = sum(s.amount for s in c_shares)
            if sum_c != new_total:
                raise bad_request(f"Sum of custom shares ({sum_c}) must equal total ({new_total}).")
            await _validate_participants_active(db, expense.group_id, u_ids)
            share_tuples = [(s.user_id, s.amount) for s in c_shares]

        # Preserve existing approval status where possible, or reset PENDING
        existing_statuses = {s.user_id: s.status for s in expense.shares}

        # Remove old shares
        for old_s in list(expense.shares):
            await db.delete(old_s)

        await db.flush()

        # Create new shares
        for uid, amt in share_tuples:
            is_owner = uid == caller.id
            prev_status = existing_statuses.get(uid, ShareStatus.PENDING)
            status = ShareStatus.APPROVED if is_owner else prev_status
            new_share = ExpenseShare(
                expense_id=expense.id,
                user_id=uid,
                amount=amt,
                status=status,
                responded_at=_now() if status != ShareStatus.PENDING else None,
            )
            db.add(new_share)

    expense.updated_at = _now()
    await db.flush()
    # Re-fetch to populate eager loads cleanly
    return await get_expense_by_id(db, expense_id=expense.id)


# ---------------------------------------------------------------------------
# Soft Delete Expense (FR10a, FR10b)
# ---------------------------------------------------------------------------


async def delete_expense(
    db: AsyncSession,
    *,
    expense_id: uuid.UUID,
    caller: User,
) -> Expense:
    """
    Soft-delete an expense (sets is_deleted=True).

    Rules:
      - Only the owner can delete (FR10).
      - Cannot delete if already deleted.
      - Cannot delete if owner_locked=True (FR10b).
      - History is NEVER physically removed from database (FR10a).
    """
    expense = await get_expense_by_id(db, expense_id=expense_id)

    if expense.owner_id != caller.id:
        raise forbidden("Only the expense owner can delete this expense (FR10).")

    if expense.is_deleted:
        raise bad_request("Expense is already deleted.")

    if expense.owner_locked:
        raise forbidden(
            "This expense is locked because the owner left the group (FR10b)."
        )

    expense.is_deleted = True
    expense.updated_at = _now()
    await db.flush()
    return expense


# ---------------------------------------------------------------------------
# Respond to Expense Share (FR12–FR14)
# ---------------------------------------------------------------------------


async def respond_to_share(
    db: AsyncSession,
    *,
    expense_id: uuid.UUID,
    caller: User,
    approve: bool,
) -> ExpenseShare:
    """
    Approve or reject a participant's expense share.

    Rules:
      - Caller must be the assigned participant of the share.
      - Cannot respond to share of a deleted expense.
    """
    result = await db.execute(
        select(ExpenseShare)
        .options(selectinload(ExpenseShare.expense))
        .where(
            ExpenseShare.expense_id == expense_id,
            ExpenseShare.user_id == caller.id,
        )
    )
    share = result.scalar_one_or_none()

    if share is None:
        raise not_found("Expense share for this user")

    if share.expense.is_deleted:
        raise bad_request("Cannot respond to share of a deleted expense.")

    share.status = ShareStatus.APPROVED if approve else ShareStatus.REJECTED
    share.responded_at = _now()

    await db.flush()
    return share
