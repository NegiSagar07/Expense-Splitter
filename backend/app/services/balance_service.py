"""
app/services/balance_service.py
--------------------------------
Business logic for group balance calculation and net debt simplification (FR16).

Rules & Filtering:
  1. Only active (non-deleted) expenses are included (`is_deleted == False`).
  2. Only APPROVED shares are included (`status == ShareStatus.APPROVED`).
     - Pending or Rejected shares are excluded from financial obligations.
  3. Net balance per user = Total amount paid as owner - Total approved shares owed.
  4. Debt Simplification (FR16):
     - Pair up debtors (net < 0) and creditors (net > 0) to produce minimal "X owes Y ₹Z" transactions.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Expense,
    ExpenseShare,
    GroupMembership,
    MemberStatus,
    ShareStatus,
    User,
)
from app.schemas.balance import GroupBalanceResponse, NetDebt, UserBalanceSummary
from app.schemas.user import UserRead


def _simplify_debts(
    net_balances: Dict[uuid.UUID, Decimal], user_map: Dict[uuid.UUID, User]
) -> list[NetDebt]:
    """
    Greedy debt simplification algorithm.
    Pairs largest debtor with largest creditor to minimize transactions (FR16).
    """
    debtors: list[list] = []   # [user_id, debt_amount (positive Decimal)]
    creditors: list[list] = [] # [user_id, credit_amount (positive Decimal)]

    for uid, net in net_balances.items():
        if net < Decimal("0.00"):
            debtors.append([uid, -net])
        elif net > Decimal("0.00"):
            creditors.append([uid, net])

    # Sort descending by amount
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    net_debts: list[NetDebt] = []

    i = 0  # debtor pointer
    j = 0  # creditor pointer

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amt = debtors[i]
        creditor_id, credit_amt = creditors[j]

        settle_amt = min(debt_amt, credit_amt).quantize(Decimal("0.01"))

        if settle_amt > Decimal("0.00"):
            d_user = user_map.get(debtor_id)
            c_user = user_map.get(creditor_id)

            net_debts.append(
                NetDebt(
                    debtor_id=debtor_id,
                    debtor=UserRead.model_validate(d_user) if d_user else None,
                    creditor_id=creditor_id,
                    creditor=UserRead.model_validate(c_user) if c_user else None,
                    amount=settle_amt,
                )
            )

        # Update remaining amounts
        debtors[i][1] -= settle_amt
        creditors[j][1] -= settle_amt

        if debtors[i][1].quantize(Decimal("0.01")) == Decimal("0.00"):
            i += 1
        if creditors[j][1].quantize(Decimal("0.01")) == Decimal("0.00"):
            j += 1

    return net_debts


async def calculate_group_balances(
    db: AsyncSession, *, group_id: uuid.UUID
) -> GroupBalanceResponse:
    """
    Calculate full balance state for a group.

    Steps:
      1. Fetch all members of the group (including left ones if they have history).
      2. Fetch all non-deleted expenses (`is_deleted=False`) with approved shares.
      3. Compute total_paid and total_owed per user.
      4. Simplify net debts.
    """
    # 1. Get all memberships for user details
    mem_result = await db.execute(
        select(GroupMembership)
        .options(selectinload(GroupMembership.user))
        .where(GroupMembership.group_id == group_id)
    )
    memberships = mem_result.scalars().all()
    user_map: Dict[uuid.UUID, User] = {m.user_id: m.user for m in memberships if m.user}

    # Initialize counters for all known members
    total_paid: Dict[uuid.UUID, Decimal] = {uid: Decimal("0.00") for uid in user_map}
    total_owed: Dict[uuid.UUID, Decimal] = {uid: Decimal("0.00") for uid in user_map}

    # 2. Fetch non-deleted expenses with shares
    exp_result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.shares))
        .where(
            Expense.group_id == group_id,
            Expense.is_deleted == False,  # noqa: E712
        )
    )
    expenses = exp_result.scalars().all()

    # 3. Process expenses and approved shares
    for exp in expenses:
        # Check owner is in map
        if exp.owner_id not in total_paid:
            total_paid[exp.owner_id] = Decimal("0.00")
            total_owed[exp.owner_id] = Decimal("0.00")

        # Accumulate total paid by owner
        total_paid[exp.owner_id] += exp.total_amount

        # Accumulate approved share amounts owed by participants
        for share in exp.shares:
            if share.status == ShareStatus.APPROVED:
                if share.user_id not in total_owed:
                    total_paid[share.user_id] = Decimal("0.00")
                    total_owed[share.user_id] = Decimal("0.00")
                total_owed[share.user_id] += share.amount

    # 4. Calculate net balances
    net_balances: Dict[uuid.UUID, Decimal] = {}
    user_summaries: list[UserBalanceSummary] = []

    for uid in total_paid:
        paid = total_paid[uid].quantize(Decimal("0.01"))
        owed = total_owed[uid].quantize(Decimal("0.01"))
        net = (paid - owed).quantize(Decimal("0.01"))

        net_balances[uid] = net

        u_obj = user_map.get(uid)
        user_summaries.append(
            UserBalanceSummary(
                user_id=uid,
                user=UserRead.model_validate(u_obj) if u_obj else None,
                total_paid=paid,
                total_owed=owed,
                net_balance=net,
            )
        )

    # 5. Simplify debts (FR16)
    net_debts = _simplify_debts(net_balances, user_map)

    return GroupBalanceResponse(
        group_id=group_id,
        user_balances=user_summaries,
        net_debts=net_debts,
    )
