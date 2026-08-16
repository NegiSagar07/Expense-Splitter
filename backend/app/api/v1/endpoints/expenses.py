"""
app/api/v1/endpoints/expenses.py
---------------------------------
Expense management endpoints:
  - Create expense in a group
  - List group expenses
  - Get expense details
  - Update expense (owner + unlocked only)
  - Soft delete expense (owner + unlocked only)
  - Respond to expense share (approve / reject)
  - Get group balance summary & net debts
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_active_membership, get_current_user
from app.db.session import get_db
from app.models.models import GroupMembership, User
from app.schemas.balance import GroupBalanceResponse
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseRead,
    ExpenseShareRead,
    ExpenseUpdate,
    RespondShareRequest,
    SettleDebtRequest,
)
from app.services import balance_service, expense_service

router = APIRouter()


# ===========================================================================
# Expense CRUD
# ===========================================================================


@router.post(
    "/groups/{group_id}/expenses",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new expense in a group",
)
async def create_expense(
    group_id: uuid.UUID,
    payload: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> ExpenseRead:
    user, _ = ctx
    expense = await expense_service.create_expense(
        db, group_id=group_id, owner=user, payload=payload
    )
    await db.commit()
    return await expense_service.get_expense_by_id(db, expense_id=expense.id)


@router.get(
    "/groups/{group_id}/expenses",
    response_model=list[ExpenseRead],
    summary="List all expenses in a group",
)
async def list_expenses(
    group_id: uuid.UUID,
    include_deleted: bool = Query(False, description="Include soft-deleted expenses in history"),
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> list[ExpenseRead]:
    return await expense_service.get_group_expenses(
        db, group_id=group_id, include_deleted=include_deleted
    )


@router.get(
    "/expenses/{expense_id}",
    response_model=ExpenseRead,
    summary="Get single expense details with shares",
)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseRead:
    expense = await expense_service.get_expense_by_id(db, expense_id=expense_id)
    # Check caller is active member of the expense's group
    await get_active_membership(expense.group_id, current_user=current_user, db=db)
    return expense


@router.patch(
    "/expenses/{expense_id}",
    response_model=ExpenseRead,
    summary="Update expense description, total amount, or split configuration (owner only)",
)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseRead:
    expense = await expense_service.update_expense(
        db, expense_id=expense_id, caller=current_user, payload=payload
    )
    await db.commit()
    return expense


@router.delete(
    "/expenses/{expense_id}",
    response_model=ExpenseRead,
    summary="Soft-delete an expense (owner only; history preserved)",
)
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseRead:
    expense = await expense_service.delete_expense(
        db, expense_id=expense_id, caller=current_user
    )
    await db.commit()
    return expense


# ===========================================================================
# Share Responses
# ===========================================================================


@router.post(
    "/expenses/{expense_id}/shares/respond",
    response_model=ExpenseShareRead,
    summary="Approve or reject your share in an expense",
)
async def respond_share(
    expense_id: uuid.UUID,
    payload: RespondShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseShareRead:
    share = await expense_service.respond_to_share(
        db, expense_id=expense_id, caller=current_user, approve=payload.approve
    )
    await db.commit()
    await db.refresh(share)
    return share


# ===========================================================================
# Balances & Debt Simplification
# ===========================================================================


@router.get(
    "/groups/{group_id}/balances",
    response_model=GroupBalanceResponse,
    summary="Get group balances and simplified net debts (approved shares + non-deleted only)",
)
async def get_group_balances(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> GroupBalanceResponse:
    return await balance_service.calculate_group_balances(db, group_id=group_id)


@router.post(
    "/groups/{group_id}/settle",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Settle debt between two group members",
)
async def settle_debt(
    group_id: uuid.UUID,
    payload: SettleDebtRequest,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> ExpenseRead:
    user, _ = ctx
    expense = await expense_service.settle_debt(
        db,
        group_id=group_id,
        caller=user,
        debtor_id=payload.debtor_id,
        creditor_id=payload.creditor_id,
        amount=payload.amount,
    )
    await db.commit()
    return expense
