"""
app/schemas/balance.py
-----------------------
Pydantic v2 schemas for group balance calculations and net debt settlements.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.user import UserRead


class NetDebt(BaseModel):
    """
    Represents a simplified debt between two users (FR16).
    `debtor` owes `amount` to `creditor`.
    """

    debtor_id: uuid.UUID
    debtor: UserRead | None = None
    creditor_id: uuid.UUID
    creditor: UserRead | None = None
    amount: Decimal


class UserBalanceSummary(BaseModel):
    """
    Per-user balance state in a group.
    net_balance > 0 means the user is owed money (creditor).
    net_balance < 0 means the user owes money (debtor).
    """

    user_id: uuid.UUID
    user: UserRead | None = None
    total_paid: Decimal
    total_owed: Decimal
    net_balance: Decimal


class GroupBalanceResponse(BaseModel):
    """Response payload for GET /groups/{group_id}/balances."""

    group_id: uuid.UUID
    user_balances: list[UserBalanceSummary]
    net_debts: list[NetDebt]
