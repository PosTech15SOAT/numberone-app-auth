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
