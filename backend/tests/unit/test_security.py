"""
tests/unit/test_security.py
----------------------------
Unit tests for password hashing and JWT token security helpers.
"""
from __future__ import annotations

import uuid
import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

settings = get_settings()


def test_password_hashing():
    raw_pass = "secret123Pass!"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_flow():
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload.get("sub") == user_id


def test_decode_invalid_jwt():
    with pytest.raises(Exception):
        decode_access_token("invalid.jwt.token.string")
