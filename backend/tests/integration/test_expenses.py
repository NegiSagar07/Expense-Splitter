"""
tests/integration/test_expenses.py
-----------------------------------
Integration tests for expense creation, share responses, soft delete, and balance calculations.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_expense_lifecycle_and_balances(async_client: AsyncClient, create_user, auth_headers):
    # Setup 2 users in a group
    alice = await create_user(name="Alice Expenses")
    bob = await create_user(name="Bob Expenses")

    a_headers = auth_headers(alice)
    b_headers = auth_headers(bob)

    # Alice creates group
    group = (await async_client.post("/api/v1/groups", headers=a_headers, json={"name": "Expense Trip"})).json()
    g_id = group["id"]

    # Bob joins group
    req = (await async_client.post(f"/api/v1/groups/{g_id}/join-requests", headers=b_headers)).json()
    await async_client.post(f"/api/v1/groups/{g_id}/join-requests/{req['id']}/approve", headers=a_headers)

    # Alice logs ₹1000 EQUAL expense for Alice & Bob
    exp_resp = await async_client.post(
        f"/api/v1/groups/{g_id}/expenses",
        headers=a_headers,
        json={
            "description": "Hotel Room",
            "total_amount": 1000.00,
            "split_type": "equal",
            "participant_ids": [str(alice.id), str(bob.id)],
        },
    )
    assert exp_resp.status_code == 201
    exp = exp_resp.json()
    exp_id = exp["id"]

    # Verify Alice's share is approved, Bob's is pending
    bob_share = next(s for s in exp["shares"] if s["user_id"] == str(bob.id))
    assert bob_share["status"] == "pending"

    # Bob approves his share
    resp_share = await async_client.post(
        f"/api/v1/expenses/{exp_id}/shares/respond",
        headers=b_headers,
        json={"approve": True},
    )
    assert resp_share.status_code == 200
    assert resp_share.json()["status"] == "approved"

    # Check group balances
    bal_resp = await async_client.get(f"/api/v1/groups/{g_id}/balances", headers=a_headers)
    assert bal_resp.status_code == 200
    bal_data = bal_resp.json()

    # Bob owes Alice ₹500
    assert len(bal_data["net_debts"]) == 1
    debt = bal_data["net_debts"][0]
    assert debt["debtor_id"] == str(bob.id)
    assert debt["creditor_id"] == str(alice.id)
    assert float(debt["amount"]) == 500.00

    # Soft delete expense
    del_resp = await async_client.delete(f"/api/v1/expenses/{exp_id}", headers=a_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_deleted"] is True

    # Active balances after soft delete should be 0
    bal_after = (await async_client.get(f"/api/v1/groups/{g_id}/balances", headers=a_headers)).json()
    assert len(bal_after["net_debts"]) == 0


@pytest.mark.asyncio
async def test_custom_split_expense(async_client: AsyncClient, create_user, auth_headers):
    user1 = await create_user(name="Custom User 1")
    user2 = await create_user(name="Custom User 2")

    h1 = auth_headers(user1)
    h2 = auth_headers(user2)

    group = (await async_client.post("/api/v1/groups", headers=h1, json={"name": "Custom Split Group"})).json()
    g_id = group["id"]

    req = (await async_client.post(f"/api/v1/groups/{g_id}/join-requests", headers=h2)).json()
    await async_client.post(f"/api/v1/groups/{g_id}/join-requests/{req['id']}/approve", headers=h1)

    exp_resp = await async_client.post(
        f"/api/v1/groups/{g_id}/expenses",
        headers=h1,
        json={
            "description": "Dinner Custom",
            "total_amount": 1000.00,
            "split_type": "custom",
            "custom_shares": [
                {"user_id": str(user1.id), "amount": 600.00},
                {"user_id": str(user2.id), "amount": 400.00},
            ],
        },
    )
    assert exp_resp.status_code == 201
    exp = exp_resp.json()
    assert exp["split_type"] == "custom"
    assert len(exp["shares"]) == 2
