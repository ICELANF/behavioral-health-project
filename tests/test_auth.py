"""
Unit tests for core/auth.py

Tests cover password hashing, JWT token lifecycle, token blacklist, and permission checks.
"""
import os
import sys
import time

import pytest

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    check_permission,
    TokenBlacklist,
)


# -----------------------------------------------
# Password hashing
# -----------------------------------------------

class TestHashPassword:
    def test_hash_password(self):
        """hash_password should return a bcrypt hash that differs from the plaintext."""
        plaintext = "Sup3rS3cret!"
        hashed = hash_password(plaintext)

        assert hashed != plaintext
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_hash_password_unique(self):
        """Two calls with the same password should produce different hashes (salted)."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestVerifyPassword:
    def test_verify_password(self):
        """verify_password should return True for a matching plaintext/hash pair."""
        plaintext = "MyP@ssw0rd"
        hashed = hash_password(plaintext)
        assert verify_password(plaintext, hashed) is True

    def test_verify_password_wrong(self):
        """verify_password should return False when the plaintext does not match."""
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


# -----------------------------------------------
# JWT tokens
# -----------------------------------------------

class TestCreateAccessToken:
    def test_create_access_token(self):
        """create_access_token should return a non-empty JWT string."""
        token = create_access_token({"user_id": 1, "username": "test"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_type(self):
        """The decoded access token should carry type='access'."""
        token = create_access_token({"user_id": 1})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["user_id"] == 1


class TestCreateRefreshToken:
    def test_create_refresh_token(self):
        """create_refresh_token should return a non-empty JWT string."""
        token = create_refresh_token({"user_id": 2, "username": "refresh_user"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_contains_type(self):
        """The decoded refresh token should carry type='refresh'."""
        token = create_refresh_token({"user_id": 2})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["user_id"] == 2


class TestDecodeToken:
    def test_decode_token(self):
        """decode_token should return the original payload fields."""
        data = {"user_id": 42, "username": "alice", "role": "patient"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["user_id"] == 42
        assert payload["username"] == "alice"
        assert payload["role"] == "patient"
        assert "exp" in payload

    def test_decode_token_invalid(self):
        """decode_token should return None for a garbage token."""
        result = decode_token("not.a.valid.token")
        assert result is None

    def test_decode_token_tampered(self):
        """decode_token should return None if the token signature is tampered."""
        token = create_access_token({"user_id": 1})
        tampered = token[:-4] + "XXXX"
        result = decode_token(tampered)
        assert result is None


class TestVerifyTokenTypeMismatch:
    def test_verify_token_type_mismatch(self):
        """verify_token should return None when the token type does not match."""
        access_token = create_access_token({"user_id": 1})
        # Attempt to verify an access token as a refresh token
        result = verify_token(access_token, token_type="refresh")
        assert result is None

    def test_verify_token_correct_type(self):
        """verify_token should return the payload when the type matches."""
        access_token = create_access_token({"user_id": 1})
        result = verify_token(access_token, token_type="access")
        assert result is not None
        assert result["user_id"] == 1

    def test_verify_refresh_token_correct_type(self):
        """verify_token should accept a refresh token when token_type='refresh'."""
        refresh_token = create_refresh_token({"user_id": 5})
        result = verify_token(refresh_token, token_type="refresh")
        assert result is not None
        assert result["user_id"] == 5


# -----------------------------------------------
# Token Blacklist
# -----------------------------------------------

class TestTokenBlacklist:
    def test_token_blacklist(self):
        """Revoking a token should cause is_revoked to return True."""
        blacklist = TokenBlacklist()
        token = create_access_token({"user_id": 99})

        assert blacklist.is_revoked(token) is False
        blacklist.revoke(token)
        assert blacklist.is_revoked(token) is True

    def test_blacklist_does_not_affect_other_tokens(self):
        """Revoking one token should not affect a different token."""
        blacklist = TokenBlacklist()
        token_a = create_access_token({"user_id": 1})
        token_b = create_access_token({"user_id": 2})

        blacklist.revoke(token_a)
        assert blacklist.is_revoked(token_a) is True
        assert blacklist.is_revoked(token_b) is False

    def test_blacklist_invalid_token_revoke(self):
        """Revoking an invalid token should not raise but should not mark anything."""
        blacklist = TokenBlacklist()
        blacklist.revoke("invalid-token")
        # Since decode_token returns None for invalid tokens, nothing is added
        # The hash of "invalid-token" is NOT in the set because revoke only adds
        # when decode succeeds.
        # Confirm that calling is_revoked on a valid token still works
        token = create_access_token({"user_id": 10})
        assert blacklist.is_revoked(token) is False


# -----------------------------------------------
# Permission checks
# -----------------------------------------------

class TestCheckPermission:
    def test_check_permission(self):
        """Admin should have permission for patient-level resources."""
        assert check_permission("admin", "patient") is True

    def test_admin_has_all_permissions(self):
        """Admin role should satisfy admin, coach, and patient requirements."""
        assert check_permission("admin", "admin") is True
        assert check_permission("admin", "coach") is True
        assert check_permission("admin", "patient") is True

    def test_patient_cannot_access_admin(self):
        """Patient role should not satisfy admin or coach requirements."""
        assert check_permission("patient", "admin") is False
        assert check_permission("patient", "coach") is False

    def test_patient_can_access_patient(self):
        """Patient role should satisfy patient-level requirements."""
        assert check_permission("patient", "patient") is True

    def test_coach_can_access_patient(self):
        """Coach role should satisfy patient-level requirements."""
        assert check_permission("coach", "patient") is True

    def test_coach_cannot_access_admin(self):
        """Coach role should not satisfy admin requirements."""
        assert check_permission("coach", "admin") is False

    def test_unknown_role(self):
        """An unknown role should default to level 0 and fail most checks."""
        assert check_permission("unknown", "patient") is False
        assert check_permission("unknown", "admin") is False
