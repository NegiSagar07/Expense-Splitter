"""
app/api/v1/endpoints/groups.py
-------------------------------
Group and membership endpoints — all routes under /groups.

Role enforcement summary (from Specs.md):
  - Any authenticated user can create a group or submit a join request.
  - Admin / Super Admin: approve/reject join requests, admin requests, promote, remove.
  - Super Admin only: remove/demote an admin (enforced in service layer).
  - Super Admin: must pass successor_id when leaving (enforced in service layer).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_admin,
    get_active_membership,
    get_current_user,
)
from app.core.exceptions import not_found
from app.db.session import get_db
from app.models.models import GroupMembership, User
from app.schemas.group import (
    GroupCreate,
    GroupDetailRead,
    GroupRead,
    LeaveGroupRequest,
    MembershipRead,
)
from app.schemas.request import AdminRequestRead, JoinRequestRead
from app.services import group_service

router = APIRouter()


# ===========================================================================
# Groups CRUD
# ===========================================================================


@router.post(
    "",
    response_model=GroupRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new group (caller becomes Super Admin)",
)
async def create_group(
    payload: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupRead:
    group = await group_service.create_group(db, name=payload.name, owner=current_user)
    await db.commit()
    await db.refresh(group)
    return group


@router.get(
    "",
    response_model=list[GroupRead],
    summary="List all groups the current user belongs to",
)
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupRead]:
    return await group_service.get_user_groups(db, user_id=current_user.id)


@router.get(
    "/{group_id}",
    response_model=GroupDetailRead,
    summary="Get group details and active member list",
)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> GroupDetailRead:
    group, members = await group_service.get_group_with_members(db, group_id=group_id)
    return GroupDetailRead(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        created_at=group.created_at,
        members=[MembershipRead.model_validate(m) for m in members],
    )


# ===========================================================================
# Join requests
# ===========================================================================


@router.post(
    "/{group_id}/join-requests",
    response_model=JoinRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a request to join a group",
)
async def submit_join_request(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JoinRequestRead:
    req = await group_service.submit_join_request(db, group_id=group_id, user=current_user)
    await db.commit()
    await db.refresh(req)
    return req


@router.get(
    "/{group_id}/join-requests",
    response_model=list[JoinRequestRead],
    summary="List pending join requests (admin+ only)",
)
async def list_join_requests(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> list[JoinRequestRead]:
    _, membership = ctx
    assert_admin(membership)
    return await group_service.get_pending_join_requests(db, group_id=group_id)


@router.post(
    "/{group_id}/join-requests/{req_id}/approve",
    response_model=JoinRequestRead,
    summary="Approve a join request (admin+ only)",
)
async def approve_join_request(
    group_id: uuid.UUID,
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> JoinRequestRead:
    user, membership = ctx
    req = await group_service.resolve_join_request(
        db, req_id=req_id, group_id=group_id,
        resolver=user, caller_membership=membership, approve=True,
    )
    await db.commit()
    await db.refresh(req)
    return req


@router.post(
    "/{group_id}/join-requests/{req_id}/reject",
    response_model=JoinRequestRead,
    summary="Reject a join request (admin+ only)",
)
async def reject_join_request(
    group_id: uuid.UUID,
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> JoinRequestRead:
    user, membership = ctx
    req = await group_service.resolve_join_request(
        db, req_id=req_id, group_id=group_id,
        resolver=user, caller_membership=membership, approve=False,
    )
    await db.commit()
    await db.refresh(req)
    return req


# ===========================================================================
# Admin-promotion requests
# ===========================================================================


@router.post(
    "/{group_id}/admin-requests",
    response_model=AdminRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Request to be promoted to Admin",
)
async def submit_admin_request(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> AdminRequestRead:
    user, membership = ctx
    req = await group_service.submit_admin_request(
        db, group_id=group_id, user=user, caller_membership=membership,
    )
    await db.commit()
    await db.refresh(req)
    return req


@router.get(
    "/{group_id}/admin-requests",
    response_model=list[AdminRequestRead],
    summary="List pending admin-promotion requests (admin+ only)",
)
async def list_admin_requests(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> list[AdminRequestRead]:
    _, membership = ctx
    assert_admin(membership)
    return await group_service.get_pending_admin_requests(db, group_id=group_id)


@router.post(
    "/{group_id}/admin-requests/{req_id}/approve",
    response_model=AdminRequestRead,
    summary="Approve an admin-promotion request (admin+ only)",
)
async def approve_admin_request(
    group_id: uuid.UUID,
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> AdminRequestRead:
    user, membership = ctx
    req = await group_service.resolve_admin_request(
        db, req_id=req_id, group_id=group_id,
        resolver=user, caller_membership=membership, approve=True,
    )
    await db.commit()
    await db.refresh(req)
    return req


@router.post(
    "/{group_id}/admin-requests/{req_id}/reject",
    response_model=AdminRequestRead,
    summary="Reject an admin-promotion request (admin+ only)",
)
async def reject_admin_request(
    group_id: uuid.UUID,
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> AdminRequestRead:
    user, membership = ctx
    req = await group_service.resolve_admin_request(
        db, req_id=req_id, group_id=group_id,
        resolver=user, caller_membership=membership, approve=False,
    )
    await db.commit()
    await db.refresh(req)
    return req


# ===========================================================================
# Member management
# ===========================================================================


@router.post(
    "/{group_id}/members/{target_user_id}/promote",
    response_model=MembershipRead,
    summary="Directly promote a member to Admin (admin+ only)",
)
async def promote_member(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> MembershipRead:
    _, membership = ctx
    target = await group_service.promote_to_admin(
        db, group_id=group_id, target_user_id=target_user_id,
        caller_membership=membership,
    )
    await db.commit()
    await db.refresh(target)
    return target


@router.post(
    "/{group_id}/members/{target_user_id}/remove",
    response_model=MembershipRead,
    summary="Remove a member from the group (admin+ only; see role rules)",
)
async def remove_member(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> MembershipRead:
    _, membership = ctx
    target = await group_service.remove_member(
        db, group_id=group_id, target_user_id=target_user_id,
        caller_membership=membership,
    )
    await db.commit()
    await db.refresh(target)
    return target


@router.post(
    "/{group_id}/leave",
    response_model=MembershipRead,
    summary="Leave the group (Super Admin must pass successor_id)",
)
async def leave_group(
    group_id: uuid.UUID,
    payload: LeaveGroupRequest = LeaveGroupRequest(),
    db: AsyncSession = Depends(get_db),
    ctx: tuple[User, GroupMembership] = Depends(get_active_membership),
) -> MembershipRead:
    user, membership = ctx
    result = await group_service.leave_group(
        db,
        group_id=group_id,
        caller=user,
        caller_membership=membership,
        successor_id=payload.successor_id,
    )
    await db.commit()
    await db.refresh(result)
    return result
