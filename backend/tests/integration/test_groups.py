"""
tests/integration/test_groups.py
---------------------------------
Integration tests for group management, join requests, admin requests, member promotion/removal, and leave group.
"""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_group(async_client: AsyncClient, create_user, auth_headers):
    user = await create_user(name="Group Creator")
    headers = auth_headers(user)

    # 1. Create group
    create_resp = await async_client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "Road Trip Group"},
    )
    assert create_resp.status_code == 201
    group_data = create_resp.json()
    assert group_data["name"] == "Road Trip Group"
    group_id = group_data["id"]

    # 2. List groups
    list_resp = await async_client.get("/api/v1/groups", headers=headers)
    assert list_resp.status_code == 200
    groups = list_resp.json()
    assert len(groups) >= 1
    assert any(g["id"] == group_id for g in groups)

    # 3. Get group detail
    detail_resp = await async_client.get(f"/api/v1/groups/{group_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["members"]) == 1
    assert detail["members"][0]["role"] == "super_admin"


@pytest.mark.asyncio
async def test_join_request_workflow(async_client: AsyncClient, create_user, auth_headers):
    creator = await create_user(name="Creator")
    applicant = await create_user(name="Applicant")

    c_headers = auth_headers(creator)
    a_headers = auth_headers(applicant)

    # Creator makes group
    group = (await async_client.post("/api/v1/groups", headers=c_headers, json={"name": "Join Test Group"})).json()
    g_id = group["id"]

    # Applicant submits join request
    req_resp = await async_client.post(f"/api/v1/groups/{g_id}/join-requests", headers=a_headers)
    assert req_resp.status_code == 201
    req_data = req_resp.json()
    req_id = req_data["id"]

    # Creator approves join request
    appr_resp = await async_client.post(f"/api/v1/groups/{g_id}/join-requests/{req_id}/approve", headers=c_headers)
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # Verify applicant is now an active member
    detail = (await async_client.get(f"/api/v1/groups/{g_id}", headers=c_headers)).json()
    assert len(detail["members"]) == 2
    assert any(m["user_id"] == str(applicant.id) for m in detail["members"])


@pytest.mark.asyncio
async def test_super_admin_leave_requires_successor(async_client: AsyncClient, create_user, auth_headers):
    super_admin = await create_user(name="SuperAdmin")
    headers = auth_headers(super_admin)

    group = (await async_client.post("/api/v1/groups", headers=headers, json={"name": "Solo Group"})).json()
    g_id = group["id"]

    # Attempt to leave without successor
    leave_resp = await async_client.post(f"/api/v1/groups/{g_id}/leave", headers=headers, json={})
    assert leave_resp.status_code == 400
    assert "designate a successor" in leave_resp.json()["detail"]


@pytest.mark.asyncio
async def test_admin_request_workflow(async_client: AsyncClient, create_user, auth_headers):
    admin = await create_user(name="Group Admin")
    member = await create_user(name="Group Member")

    a_headers = auth_headers(admin)
    m_headers = auth_headers(member)

    # Admin creates group
    group = (await async_client.post("/api/v1/groups", headers=a_headers, json={"name": "Admin Test Group"})).json()
    g_id = group["id"]

    # Member joins
    req = (await async_client.post(f"/api/v1/groups/{g_id}/join-requests", headers=m_headers)).json()
    await async_client.post(f"/api/v1/groups/{g_id}/join-requests/{req['id']}/approve", headers=a_headers)

    # Member requests admin promotion
    admin_req = (await async_client.post(f"/api/v1/groups/{g_id}/admin-requests", headers=m_headers)).json()
    assert admin_req["status"] == "pending"

    # Admin approves promotion
    appr = (await async_client.post(f"/api/v1/groups/{g_id}/admin-requests/{admin_req['id']}/approve", headers=a_headers)).json()
    assert appr["status"] == "approved"

    # Verify member is now admin
    detail = (await async_client.get(f"/api/v1/groups/{g_id}", headers=a_headers)).json()
    m_role = next(m["role"] for m in detail["members"] if m["user_id"] == str(member.id))
    assert m_role == "admin"
