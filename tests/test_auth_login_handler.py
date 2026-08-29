import json
from uuid import uuid4

from src.auth_login import handler


def test_auth_login_returns_token_for_active_customer(monkeypatch) -> None:
    customer_id = uuid4()
    user_id = uuid4()

    monkeypatch.setattr(
        handler,
        "find_active_customer_by_cpf",
        lambda cpf: {
            "id": customer_id,
            "nome": "Joao da Silva",
            "documento": cpf,
            "email": "joao@example.com",
            "ativo": True,
        },
    )
    monkeypatch.setattr(
        handler,
        "find_or_create_auth_user",
        lambda customer, cpf: {
            "id": user_id,
            "cliente_id": customer["id"],
            "cpf": cpf,
            "nome": customer["nome"],
            "email": customer["email"],
            "ativo": True,
        },
    )
    monkeypatch.setattr(
        handler,
        "find_rbac_claims",
        lambda auth_user_id: {
            "roles": ["CUSTOMER"],
            "permissions": ["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"],
        },
    )
    monkeypatch.setattr(
        handler,
        "issue_token",
        lambda **kwargs: ("token", 3600),
    )

    result = handler.lambda_handler(
        {"body": json.dumps({"cpf": "123.456.789-09"})},
        None,
    )

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {
        "accessToken": "token",
        "tokenType": "Bearer",
        "expiresIn": 3600,
    }


def test_auth_login_rejects_invalid_cpf() -> None:
    result = handler.lambda_handler({"body": json.dumps({"cpf": "11111111111"})}, None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["message"] == "CPF invalido."


def test_auth_login_returns_not_found_when_customer_does_not_exist(monkeypatch) -> None:
    monkeypatch.setattr(handler, "find_active_customer_by_cpf", lambda cpf: None)

    result = handler.lambda_handler(
        {"body": json.dumps({"cpf": "123.456.789-09"})},
        None,
    )

    assert result["statusCode"] == 404
    assert json.loads(result["body"])["message"] == "Cliente nao encontrado."


def test_auth_login_rejects_invalid_json() -> None:
    result = handler.lambda_handler({"body": "{"}, None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["message"] == "Request invalido."
