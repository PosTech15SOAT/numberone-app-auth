import json
from uuid import uuid4

import pytest

from src.auth_login import handler
from src.shared.jwt_service import validate_token
from src.shared.password import hash_password

PASSWORD = "synthetic-user-password"


def login(body, correlation="synthetic-correlation"):
    return handler.lambda_handler(
        {"headers": {"X-Correlation-Id": correlation}, "body": json.dumps(body)}, None
    )


def test_customer_requires_password_and_active_os_link(signing, monkeypatch):
    user, owner = uuid4(), uuid4()
    account = {
        "id": user,
        "cliente_id": owner,
        "senha_hash": hash_password(PASSWORD),
        "permissions": ["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"],
    }
    monkeypatch.setattr(
        handler,
        "find_login_identity",
        lambda cpf, role: account if (cpf, role) == ("52998224725", "CUSTOMER") else None,
    )
    monkeypatch.setattr(
        handler, "matches_active_customer",
        lambda uuid, cpf: (uuid, cpf) == (str(owner), "52998224725"),
    )

    result = login({"cpf": "529.982.247-25", "password": PASSWORD})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    claims = validate_token(body["accessToken"])
    assert claims["sub"] == str(user)
    assert claims["customer_id"] == str(owner)
    assert claims["roles"] == ["CUSTOMER"]
    assert claims["permissions"] == ["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"]

    assert login({"cpf": "529.982.247-25"})["statusCode"] == 401
    assert login({"cpf": "529.982.247-25", "password": "wrong-user-password"})["statusCode"] == 401
    account["cliente_id"] = uuid4()
    assert login({"cpf": "529.982.247-25", "password": PASSWORD})["statusCode"] == 401


def test_operator_is_separately_provisioned(signing, monkeypatch):
    account = {
        "id": uuid4(), "cliente_id": None, "senha_hash": hash_password(PASSWORD),
        "permissions": ["ADMIN_ACCESS"],
    }
    monkeypatch.setattr(
        handler, "find_login_identity",
        lambda cpf, role: account if (cpf, role) == ("11144477735", "ADMIN") else None,
    )

    assert login({"cpf": "11144477735", "password": PASSWORD})["statusCode"] == 401
    result = login({"cpf": "11144477735", "password": PASSWORD, "identityType": "OPERATOR"})
    assert result["statusCode"] == 200
    claims = validate_token(json.loads(result["body"])["accessToken"])
    assert claims["roles"] == ["ADMIN"]
    assert claims["customer_id"] is None
    assert claims["permissions"] == ["ADMIN_ACCESS"]


@pytest.mark.parametrize("body", [[], "value", {"cpf": 42}, {"cpf": "11111111111"}])
def test_invalid_login_body_or_cpf(body):
    assert login(body)["statusCode"] == 400


def test_auth_login_rejects_invalid_json():
    result = handler.lambda_handler(
        {"headers": {"X-Correlation-Id": "synthetic-correlation"}, "body": "{"}, None
    )
    assert result["statusCode"] == 400


@pytest.mark.parametrize("headers", [{}, {"x-correlation-id": " "}])
def test_auth_login_requires_nonblank_correlation_id(headers):
    result = handler.lambda_handler({"headers": headers, "body": "{}"}, None)
    assert result["statusCode"] == 400
    assert json.loads(result["body"])["message"] == "X-Correlation-Id header is required"
