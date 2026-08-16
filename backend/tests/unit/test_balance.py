"""
tests/unit/test_balance.py
---------------------------
Unit tests for equal split remainder division and greedy debt simplification algorithms.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from app.services.balance_service import _simplify_debts
from app.services.expense_service import _compute_equal_shares


def test_equal_split_remainder_handling():
    # Split 100.00 among 3 participants -> 33.34, 33.33, 33.33 -> sum == 100.00
    u1, u2, u3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    shares = _compute_equal_shares(Decimal("100.00"), [u1, u2, u3])

    assert len(shares) == 3
    total = sum(s[1] for s in shares)
    assert total == Decimal("100.00")
    assert shares[0][1] == Decimal("33.34")
    assert shares[1][1] == Decimal("33.33")
    assert shares[2][1] == Decimal("33.33")


def test_debt_simplification_greedy():
    u_alice = uuid.uuid4()
    u_bob = uuid.uuid4()
    u_charlie = uuid.uuid4()

    user_map = {}

    # Alice +1000, Bob -400, Charlie -600
    net_balances = {
        u_alice: Decimal("1000.00"),
        u_bob: Decimal("-400.00"),
        u_charlie: Decimal("-600.00"),
    }

    debts = _simplify_debts(net_balances, user_map)

    assert len(debts) == 2
    # Bob owes Alice 400, Charlie owes Alice 600
    debtor_ids = {d.debtor_id for d in debts}
    creditor_ids = {d.creditor_id for d in debts}

    assert debtor_ids == {u_bob, u_charlie}
    assert creditor_ids == {u_alice}
    assert sum(d.amount for d in debts) == Decimal("1000.00")
