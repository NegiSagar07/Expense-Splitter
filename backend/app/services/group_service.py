"""
app/services/group_service.py
------------------------------
Business logic for group management, membership, and all role operations.

All spec rules enforced here (FR2, FR3, FR4, FR-A1–FR-A6, FR6, FR10b):
  - Creator becomes super_admin on group creation (FR2)
  - Join requests require admin approval (FR3/FR4)
  - Exactly one super_admin per group at all times (FR-A1)
  - Admin promotion paths: request + approve OR direct assign (FR-A2)
  - Admin cannot remove/demote another admin (FR-A3/A4)
  - Super Admin must designate successor before leaving (FR-A6)
  - Leaving locks all expenses owned by the departing user (FR10b)
  - History preserved: memberships kept with status='left' (FR6)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, conflict, forbidden, not_found
from app.models.models import (
    AdminRequest,
    AdminRequestStatus,
    Expense,
    Group,
    GroupMembership,
    JoinRequest,
    JoinRequestStatus,
    MemberRole,
    MemberStatus,
    User,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_active_membership(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMembership | None:
    result = await db.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
            GroupMembership.status == MemberStatus.ACTIVE,
        )
    )
    return result.scalar_one_or_none()


async def _lock_user_expenses(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """
    Set owner_locked=True on all non-deleted expenses owned by this user
    in this group. Called when the expense owner leaves (FR10b).
    """
    await db.execute(
        update(Expense)
        .where(
            Expense.group_id == group_id,
            Expense.owner_id == user_id,
            Expense.is_deleted == False,  # noqa: E712
        )
        .values(owner_locked=True)
    )


async def _mark_left(membership: GroupMembership) -> None:
    membership.status = MemberStatus.LEFT
    membership.left_at = _now()


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------


async def create_group(
    db: AsyncSession,
    *,
    name: str,
    owner: User,
) -> Group:
    """
    Create a new group and add the owner as its Super Admin (FR2).
    """
    group = Group(name=name, created_by=owner.id)
    db.add(group)
    await db.flush()

    membership = GroupMembership(
        group_id=group.id,
        user_id=owner.id,
        role=MemberRole.SUPER_ADMIN,
        status=MemberStatus.ACTIVE,
    )
    db.add(membership)
    await db.flush()
    return group


async def get_user_groups(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[Group]:
    """Return all groups where the user has an active membership."""
    result = await db.execute(
        select(Group)
        .join(GroupMembership, GroupMembership.group_id == Group.id)
        .where(
            GroupMembership.user_id == user_id,
            GroupMembership.status == MemberStatus.ACTIVE,
        )
        .order_by(Group.created_at.desc())
    )
    return list(result.scalars().all())


async def get_group_with_members(
    db: AsyncSession, *, group_id: uuid.UUID
) -> tuple[Group, list[GroupMembership]]:
    """
    Return the group and its active memberships (with user data joined).
    Raises 404 if the group does not exist.
    """
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise not_found("Group")

    mem_result = await db.execute(
        select(GroupMembership)
        .where(
            GroupMembership.group_id == group_id,
            GroupMembership.status == MemberStatus.ACTIVE,
        )
        .order_by(GroupMembership.joined_at)
    )
    members = list(mem_result.scalars().all())
    return group, members


# ---------------------------------------------------------------------------
# Join requests (FR3, FR4, FR4a)
# ---------------------------------------------------------------------------


async def submit_join_request(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    user: User,
) -> JoinRequest:
    """
    Submit a join request for a group the user is not already in.

    Raises:
        409 — user is already an active member
        409 — a pending request already exists
    """
    # Already a member?
    if await _get_active_membership(db, group_id, user.id) is not None:
        raise conflict("You are already an active member of this group.")

    # Pending request already exists? (enforced by partial unique index too)
    existing = await db.execute(
        select(JoinRequest).where(
            JoinRequest.group_id == group_id,
            JoinRequest.user_id == user.id,
            JoinRequest.status == JoinRequestStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise conflict("You already have a pending join request for this group.")

    req = JoinRequest(group_id=group_id, user_id=user.id)
    db.add(req)
    await db.flush()
    return req


async def resolve_join_request(
    db: AsyncSession,
    *,
    req_id: uuid.UUID,
    group_id: uuid.UUID,
    resolver: User,
    caller_membership: GroupMembership,
    approve: bool,
) -> JoinRequest:
    """
    Approve or reject a pending join request.
    Caller must be admin or super_admin.

    On approval: creates a new GroupMembership with role=member.
    """
    # Caller must be admin+
    if caller_membership.role not in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise forbidden("Admin or Super Admin role required.")

    result = await db.execute(
        select(JoinRequest).where(
            JoinRequest.id == req_id,
            JoinRequest.group_id == group_id,
            JoinRequest.status == JoinRequestStatus.PENDING,
        )
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise not_found("Pending join request")

    req.status = JoinRequestStatus.APPROVED if approve else JoinRequestStatus.REJECTED
    req.resolved_at = _now()
    req.resolved_by = resolver.id

    if approve:
        membership = GroupMembership(
            group_id=group_id,
            user_id=req.user_id,
            role=MemberRole.MEMBER,
            status=MemberStatus.ACTIVE,
        )
        db.add(membership)

    await db.flush()
    return req


async def get_pending_join_requests(
    db: AsyncSession, *, group_id: uuid.UUID
) -> list[JoinRequest]:
    result = await db.execute(
        select(JoinRequest).where(
            JoinRequest.group_id == group_id,
            JoinRequest.status == JoinRequestStatus.PENDING,
        ).order_by(JoinRequest.requested_at)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Admin-promotion requests (FR-A2)
# ---------------------------------------------------------------------------


async def submit_admin_request(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    user: User,
    caller_membership: GroupMembership,
) -> AdminRequest:
    """
    A member requests to be promoted to Admin.

    Raises:
        409 — caller is already an admin or super_admin
        409 — a pending admin request already exists
    """
    if caller_membership.role in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise conflict("You are already an admin.")

    existing = await db.execute(
        select(AdminRequest).where(
            AdminRequest.group_id == group_id,
            AdminRequest.user_id == user.id,
            AdminRequest.status == AdminRequestStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise conflict("You already have a pending admin request for this group.")

    req = AdminRequest(group_id=group_id, user_id=user.id)
    db.add(req)
    await db.flush()
    return req


async def resolve_admin_request(
    db: AsyncSession,
    *,
    req_id: uuid.UUID,
    group_id: uuid.UUID,
    resolver: User,
    caller_membership: GroupMembership,
    approve: bool,
) -> AdminRequest:
    """
    Approve or reject a pending admin-promotion request.
    Caller must be admin or super_admin.
    """
    if caller_membership.role not in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise forbidden("Admin or Super Admin role required.")

    result = await db.execute(
        select(AdminRequest).where(
            AdminRequest.id == req_id,
            AdminRequest.group_id == group_id,
            AdminRequest.status == AdminRequestStatus.PENDING,
        )
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise not_found("Pending admin request")

    req.status = (
        AdminRequestStatus.APPROVED if approve else AdminRequestStatus.REJECTED
    )
    req.resolved_at = _now()
    req.resolved_by = resolver.id

    if approve:
        # Upgrade the requester's role to admin
        mem_result = await db.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == req.user_id,
                GroupMembership.status == MemberStatus.ACTIVE,
            )
        )
        target_mem = mem_result.scalar_one_or_none()
        if target_mem:
            target_mem.role = MemberRole.ADMIN

    await db.flush()
    return req


async def get_pending_admin_requests(
    db: AsyncSession, *, group_id: uuid.UUID
) -> list[AdminRequest]:
    result = await db.execute(
        select(AdminRequest).where(
            AdminRequest.group_id == group_id,
            AdminRequest.status == AdminRequestStatus.PENDING,
        ).order_by(AdminRequest.requested_at)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Direct promotion (FR-A2 — without a request)
# ---------------------------------------------------------------------------


async def promote_to_admin(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    caller_membership: GroupMembership,
) -> GroupMembership:
    """
    Directly promote a regular member to Admin without a formal request.
    Caller must be admin or super_admin.

    Raises:
        403 — caller is not admin+
        404 — target user is not an active member
        409 — target is already admin or super_admin
    """
    if caller_membership.role not in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise forbidden("Admin or Super Admin role required.")

    target = await _get_active_membership(db, group_id, target_user_id)
    if target is None:
        raise not_found("Target member")
    if target.role in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise conflict("This user is already an admin or super admin.")

    target.role = MemberRole.ADMIN
    await db.flush()
    return target


# ---------------------------------------------------------------------------
# Remove member (FR-A3, FR-A4)
# ---------------------------------------------------------------------------


async def remove_member(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    caller_membership: GroupMembership,
) -> GroupMembership:
    """
    Remove a member from the group.

    Rules (FR-A3, FR-A4):
      - Super Admin can remove anyone (except themselves via this route).
      - Admin can remove regular members only — NOT another admin.
      - No one can remove the Super Admin via this endpoint.

    History is preserved: status set to 'left', expenses locked.
    """
    # Caller must be at least admin
    if caller_membership.role not in (MemberRole.ADMIN, MemberRole.SUPER_ADMIN):
        raise forbidden("Admin or Super Admin role required.")

    # Can't remove yourself via this endpoint — use /leave instead
    if target_user_id == caller_membership.user_id:
        raise bad_request("Use the /leave endpoint to leave the group yourself.")

    target = await _get_active_membership(db, group_id, target_user_id)
    if target is None:
        raise not_found("Target member")

    # Super Admin cannot be removed by anyone through this route
    if target.role == MemberRole.SUPER_ADMIN:
        raise forbidden("The Super Admin cannot be removed from the group.")

    # Regular Admin can only remove members, not other admins (FR-A3)
    if target.role == MemberRole.ADMIN and caller_membership.role != MemberRole.SUPER_ADMIN:
        raise forbidden("Only the Super Admin can remove another admin (FR-A3/A4).")

    await _mark_left(target)
    await _lock_user_expenses(db, group_id, target_user_id)
    await db.flush()
    return target


# ---------------------------------------------------------------------------
# Leave group (FR-A5, FR-A6)
# ---------------------------------------------------------------------------


async def leave_group(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    caller: User,
    caller_membership: GroupMembership,
    successor_id: uuid.UUID | None,
) -> GroupMembership:
    """
    Let the current user leave a group.

    FR-A5: Admins and members can leave freely.
    FR-A6: Super Admin MUST provide a valid successor_id — the successor
           must be an active member of the group (can be a regular member;
           they will be promoted to super_admin automatically).

    On leave:
      - Membership status → 'left', left_at → now
      - All owned expenses in this group → owner_locked = True (FR10b)
      - If super_admin: successor's role → super_admin
    """
    if caller_membership.role == MemberRole.SUPER_ADMIN:
        # Successor is mandatory (FR-A6)
        if successor_id is None:
            raise bad_request(
                "As Super Admin you must designate a successor before leaving. "
                "Provide 'successor_id' in the request body."
            )
        if successor_id == caller.id:
            raise bad_request("Successor must be a different member.")

        successor = await _get_active_membership(db, group_id, successor_id)
        if successor is None:
            raise not_found("Successor member")

        # Transfer super_admin role
        successor.role = MemberRole.SUPER_ADMIN

    await _mark_left(caller_membership)
    await _lock_user_expenses(db, group_id, caller.id)
    await db.flush()
    return caller_membership
