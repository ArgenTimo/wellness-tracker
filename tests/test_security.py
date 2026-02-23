"""Security module unit tests."""

import pytest
from app.core.security import decode_token, get_password_hash, verify_password


def test_password_hash_roundtrip():
    """Password hashing and verification work correctly."""
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_decode_invalid_token():
    """Invalid token returns None."""
    assert decode_token("invalid.jwt.token") is None
    assert decode_token("") is None
