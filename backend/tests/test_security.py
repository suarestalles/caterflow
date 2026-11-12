from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_store_plaintext():
    password = "CaterFlow-Secure-Password-123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2id$")


def test_verify_password_with_correct_password():
    password = "CaterFlow-Secure-Password-123"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_password_with_incorrect_password():
    hashed_password = hash_password("Correct-Password-123")

    assert verify_password("Incorrect-Password-123", hashed_password) is False


def test_create_and_decode_access_token():
    user_id = "user-uuid"
    tenant_id = "tenant-uuid"

    token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
    )

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["tenant_id"] == tenant_id
    assert payload["type"] == "access"


def test_access_token_without_tenant():
    token = create_access_token(subject="user-uuid")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-uuid"
    assert "tenant_id" not in payload


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="user-uuid",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_signed_with_another_secret_is_rejected():
    token = jwt.encode(
        {
            "sub": "user-uuid",
            "type": "access",
            "iat": 1,
            "exp": 4_102_444_800,
        },
        "another-test-secret-key-with-32-bytes-minimum",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
