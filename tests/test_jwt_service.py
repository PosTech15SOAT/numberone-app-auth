from uuid import uuid4

import jwt
import pytest

from src.shared.jwt_service import issue_token, validate_token


def customer_token():
    return issue_token(
        subject=str(uuid4()), customer_id=str(uuid4()), cpf="52998224725",
        roles=["CUSTOMER"], permissions=["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"],
    )


def test_issue_and_verify_with_jwt_library(signing):
    token, expires_in = customer_token()
    independently_verified = jwt.decode(
        token, signing["secret"], algorithms=["HS256"],
        issuer=signing["issuer"], audience=signing["audience"],
    )
    assert validate_token(token) == independently_verified
    assert independently_verified["exp"] - independently_verified["iat"] == expires_in == 900
    assert independently_verified["status"] == "ACTIVE"


@pytest.mark.parametrize(("name", "value"), [
    ("sub", "not-a-uuid"),
    ("customer_id", None),
    ("customer_id", "not-a-uuid"),
    ("cpf", "11111111111"),
    ("roles", ["CUSTOMER", "ADMIN"]),
    ("role", "ADMIN"),
    ("status", "INACTIVE"),
    ("permissions", "SERVICE_ORDER_TRACK_OWN"),
    ("permissions", ["a,b"]),
    ("permissions", ["a", "a"]),
    ("iss", "another-issuer"),
    ("aud", "another-api"),
    ("iat", "0"),
    ("exp", 1),
])
def test_rejects_invalid_claims_even_with_valid_signature(signing, name, value):
    token, _ = customer_token()
    claims = validate_token(token)
    claims[name] = value
    with pytest.raises(jwt.PyJWTError):
        validate_token(jwt.encode(claims, signing["secret"], algorithm="HS256"))


@pytest.mark.parametrize("name", ["exp", "customer_id", "iat", "iss", "aud", "status"])
def test_rejects_missing_claims(signing, name):
    token, _ = customer_token()
    claims = validate_token(token)
    del claims[name]
    with pytest.raises(jwt.PyJWTError):
        validate_token(jwt.encode(claims, signing["secret"], algorithm="HS256"))


def test_rejects_different_signing_algorithm(signing):
    token, _ = customer_token()
    claims = validate_token(token)
    with pytest.raises(jwt.PyJWTError):
        validate_token(jwt.encode(claims, signing["secret"], algorithm="HS512"))
