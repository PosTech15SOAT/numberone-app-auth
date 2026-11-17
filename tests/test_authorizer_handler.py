import json
from uuid import uuid4

import pytest

from src.auth_login import handler as login_handler
from src.authorizer import handler
from src.shared.password import hash_password

ADMIN_ROUTE = "POST /api/admin/clientes"
TRACKING_ROUTE = "GET /api/public/ordens-servico/{id}/acompanhamento"
HISTORY_ROUTE = "GET /api/public/veiculos/{vehicleId}/historico-manutencoes"
UNAUTHORIZED = {"errorMessage": "Unauthorized"}
FORBIDDEN = {"isAuthorized": False, "context": {}}


@pytest.fixture
def identities(signing, monkeypatch):
    password = "synthetic-login-credential"
    password_hash = hash_password(password)
    rows = [
        {
            "id": uuid4(), "cliente_id": None, "perfil": "ADMIN", "cpf": "11144477735",
            "senha_hash": password_hash, "permissions": ["ADMIN_ACCESS"],
        },
        {
            "id": uuid4(), "cliente_id": uuid4(), "perfil": "CUSTOMER", "cpf": "52998224725",
            "senha_hash": password_hash, "permissions": ["SERVICE_ORDER_TRACK_OWN"],
        },
    ]
    monkeypatch.setattr(
        login_handler, "find_login_identity",
        lambda cpf, role: next(
            (row for row in rows if (row["cpf"], row["perfil"]) == (cpf, role)), None
        ),
    )
    monkeypatch.setattr(
        handler, "find_token_identity",
        lambda sub: next((row for row in rows if str(row["id"]) == sub), None),
    )
    for module in (login_handler, handler):
        monkeypatch.setattr(
            module, "matches_active_customer",
            lambda customer_id, cpf: (customer_id, cpf)
            == (str(rows[1]["cliente_id"]), rows[1]["cpf"]),
        )
    return rows, password


def login(row, password, identity_type):
    result = login_handler.lambda_handler({
        "headers": {"X-Correlation-Id": "synthetic-correlation"},
        "body": json.dumps({
            "cpf": row["cpf"], "password": password, "identityType": identity_type,
        }),
    }, None)
    assert result["statusCode"] == 200
    return json.loads(result["body"])["accessToken"]


def authorize(token, route=ADMIN_ROUTE, **headers):
    if token:
        headers["authorization"] = f"bearer {token}"
    return handler.lambda_handler({"routeKey": route, "headers": headers}, None)


def test_same_admin_route_accepts_operator_and_denies_customer_jwt(identities):
    (operator, customer), password = identities
    operator_token = login(operator, password, "OPERATOR")
    customer_token = login(customer, password, "CUSTOMER")

    allowed = authorize(operator_token, **{"X-CORRELATION-ID": "correlation"})
    assert allowed["isAuthorized"]
    assert allowed["context"]["principalId"] == str(operator["id"])
    assert allowed["context"]["roles"] == "ADMIN"
    assert allowed["context"]["customerId"] == ""
    assert allowed["context"]["correlationId"] == "correlation"
    assert authorize(customer_token, **{"X-Authenticated-Roles": "ADMIN"}) == FORBIDDEN
    assert authorize(None) == UNAUTHORIZED
    assert authorize(operator_token + "invalid") == UNAUTHORIZED


def test_customer_only_enters_explicit_tracking_routes(identities):
    (_, customer), password = identities
    token = login(customer, password, "CUSTOMER")
    for route in (TRACKING_ROUTE, HISTORY_ROUTE):
        allowed = authorize(token, route, **{"x-correlation-id": " "})
        assert allowed["isAuthorized"]
        assert allowed["context"]["customerId"] == str(customer["cliente_id"])
        assert allowed["context"]["userStatus"] == "ACTIVE"
        assert "correlationId" not in allowed["context"]
    assert authorize(token, "$default") == FORBIDDEN
    assert authorize(token, "GET /internal/auth/customer-identity") == FORBIDDEN
    assert authorize(token, "POST /api/public/ordens-servico/{id}/acompanhamento") == FORBIDDEN


def test_admin_profile_without_permission_is_denied(identities):
    (operator, _), password = identities
    operator["permissions"] = []
    assert authorize(login(operator, password, "OPERATOR")) == FORBIDDEN


def test_authorizer_checks_current_permissions_and_link(identities, monkeypatch):
    (_, customer), password = identities
    token = login(customer, password, "CUSTOMER")

    monkeypatch.setattr(handler, "matches_active_customer", lambda *_: False)
    assert authorize(token, TRACKING_ROUTE) == UNAUTHORIZED
    customer["permissions"] = []
    assert authorize(token, TRACKING_ROUTE) == UNAUTHORIZED


def test_deleted_or_disabled_subject_is_unauthorized(identities, monkeypatch):
    (operator, _), password = identities
    token = login(operator, password, "OPERATOR")
    monkeypatch.setattr(handler, "find_token_identity", lambda _: None)
    assert authorize(token) == UNAUTHORIZED


def use_http_identity_client(monkeypatch):
    from src.shared.os_identity import matches_active_customer

    for module in (login_handler, handler):
        monkeypatch.setattr(module, "matches_active_customer", matches_active_customer)


@pytest.mark.parametrize("invalid_link", ["inactive", "different_cpf"])
def test_login_and_authorizer_use_private_os_identity(
    identities, os_service, monkeypatch, invalid_link,
):
    (_, customer), password = identities
    os_service["customer_id"] = str(customer["cliente_id"])
    use_http_identity_client(monkeypatch)
    token = login(customer, password, "CUSTOMER")
    assert authorize(token, TRACKING_ROUTE)["isAuthorized"]

    rejected = login_handler.lambda_handler({
        "headers": {"X-Correlation-Id": "test-correlation"},
        "body": json.dumps({"cpf": customer["cpf"], "password": "invalid-password"}),
    }, None)
    assert rejected["statusCode"] == 401
    assert len(os_service["requests"]) == 2

    if invalid_link == "inactive":
        os_service["active"] = False
    else:
        os_service["cpf"] = "11144477735"
    assert authorize(token, TRACKING_ROUTE) == UNAUTHORIZED
    rejected = login_handler.lambda_handler({
        "headers": {"X-Correlation-Id": "test-correlation"},
        "body": json.dumps({"cpf": customer["cpf"], "password": password}),
    }, None)
    assert rejected["statusCode"] == 401
    for path, headers, body in os_service["requests"]:
        assert path == "/internal/auth/customer-identity"
        assert "Authorization" not in headers
        assert headers["X-Correlation-Id"]
        assert body == {"customerId": str(customer["cliente_id"]), "cpf": customer["cpf"]}


@pytest.mark.parametrize("status", [302, 500, 503])
def test_os_failure_never_grants_login_or_authorization(
    identities, os_service, monkeypatch, status,
):
    (_, customer), password = identities
    os_service["customer_id"] = str(customer["cliente_id"])
    use_http_identity_client(monkeypatch)
    token = login(customer, password, "CUSTOMER")
    os_service["status"] = status
    rejected = login_handler.lambda_handler({
        "headers": {"X-Correlation-Id": "test-correlation"},
        "body": json.dumps({"cpf": customer["cpf"], "password": password}),
    }, None)
    assert rejected["statusCode"] == 500
    with pytest.raises(RuntimeError, match="Authorization dependency unavailable"):
        authorize(token, TRACKING_ROUTE)
    assert len(os_service["requests"]) == 3
    assert all(path == "/internal/auth/customer-identity" for path, *_ in os_service["requests"])


def test_expired_jwt_is_rejected_before_os_lookup(identities, signing, monkeypatch):
    import jwt

    (_, customer), password = identities
    token = login(customer, password, "CUSTOMER")
    claims = jwt.decode(
        token, signing["secret"], algorithms=["HS256"], audience=signing["audience"],
    )
    claims["exp"] = 1
    expired = jwt.encode(claims, signing["secret"], algorithm="HS256")

    def unexpected_lookup(*args):
        pytest.fail("Expired JWT must not reach OS identity lookup")

    monkeypatch.setattr(handler, "matches_active_customer", unexpected_lookup)
    assert authorize(expired, TRACKING_ROUTE) == UNAUTHORIZED


def test_os_timeout_never_grants_access(identities, monkeypatch):
    from unittest.mock import Mock

    from src.shared import os_identity

    (_, customer), password = identities
    token = login(customer, password, "CUSTOMER")
    use_http_identity_client(monkeypatch)
    os_identity._settings.cache_clear()
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", "http://10.0.0.10")
    opener = Mock()
    opener.open.side_effect = TimeoutError()
    monkeypatch.setattr(os_identity, "build_opener", lambda *args: opener)
    try:
        rejected = login_handler.lambda_handler({
            "headers": {"X-Correlation-Id": "test-correlation"},
            "body": json.dumps({"cpf": customer["cpf"], "password": password}),
        }, None)
        assert rejected["statusCode"] == 500
        with pytest.raises(RuntimeError, match="Authorization dependency unavailable"):
            authorize(token, TRACKING_ROUTE)
    finally:
        os_identity._settings.cache_clear()
