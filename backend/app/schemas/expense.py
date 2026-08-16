"""
app/schemas/expense.py
-----------------------
Pydantic v2 schemas for expense creation, editing, share responses, and read views.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.models import ShareStatus, SplitType
from app.schemas.user import UserRead


# ---------------------------------------------------------------------------
# Expense Shares
# ---------------------------------------------------------------------------


class CustomShareInput(BaseModel):
    """Custom share entry for CUSTOM split type."""

    user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)


class ExpenseShareRead(BaseModel):
    """Read representation of a participant's expense share."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    status: ShareStatus
    responded_at: datetime | None = None
    user: UserRead | None = None


class RespondShareRequest(BaseModel):
    """Payload for responding to (approving or rejecting) an expense share."""

    approve: bool


# ---------------------------------------------------------------------------
# Expense CRUD Payload Schemas
# ---------------------------------------------------------------------------


class ExpenseCreate(BaseModel):
    """
    Payload for POST /groups/{group_id}/expenses.

    For EQUAL split:
        Provide `participant_ids` (list of user UUIDs). The total_amount is divided evenly.

    For CUSTOM split:
        Provide `custom_shares` (list of CustomShareInput). The sum must equal total_amount.
    """

    description: str = Field(..., min_length=1, max_length=500)
    total_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    split_type: SplitType
    participant_ids: list[uuid.UUID] | None = None
    custom_shares: list[CustomShareInput] | None = None

    @model_validator(mode="after")
    def validate_split_inputs(self) -> ExpenseCreate:
        if self.split_type == SplitType.EQUAL:
            if not self.participant_ids or len(self.participant_ids) == 0:
                raise ValueError("participant_ids is required for EQUAL split.")
            if len(self.participant_ids) != len(set(self.participant_ids)):
                raise ValueError("Duplicate participant_ids are not allowed.")
        elif self.split_type == SplitType.CUSTOM:
            if not self.custom_shares or len(self.custom_shares) == 0:
                raise ValueError("custom_shares is required for CUSTOM split.")
            user_ids = [s.user_id for s in self.custom_shares]
            if len(user_ids) != len(set(user_ids)):
                raise ValueError("Duplicate user_ids in custom_shares are not allowed.")
            total_shares_sum = sum(s.amount for s in self.custom_shares)
            if total_shares_sum != self.total_amount:
                raise ValueError(
                    f"Sum of custom shares ({total_shares_sum}) must equal total_amount ({self.total_amount})."
                )
        return self


class ExpenseUpdate(BaseModel):
    """
    Payload for PATCH /expenses/{expense_id}.
    All fields are optional. If total_amount or split parameters change, shares are recomputed.
    """

    description: str | None = Field(None, min_length=1, max_length=500)
    total_amount: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    split_type: SplitType | None = None
    participant_ids: list[uuid.UUID] | None = None
    custom_shares: list[CustomShareInput] | None = None


# ---------------------------------------------------------------------------
# Expense Read Schemas
# ---------------------------------------------------------------------------


class ExpenseRead(BaseModel):
    """Full expense details including shares."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    owner_id: uuid.UUID
    description: str
    total_amount: Decimal
    split_type: SplitType
    is_deleted: bool
    owner_locked: bool
    created_at: datetime
    updated_at: datetime
    owner: UserRead | None = None
    shares: list[ExpenseShareRead] = []
