from src.authorizer import handler


def test_authorizer_allows_valid_bearer_token(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "customer_id": "customer-id",
            "cpf": "12345678909",
            "role": "CLIENTE",
            "roles": ["CLIENTE"],
            "permissions": ["ordem-servico:read"],
        },
    )

    result = handler.lambda_handler(
        {"headers": {"Authorization": "Bearer valid-token"}},
        None,
    )

    assert result["isAuthorized"] is True
    assert result["context"]["principalId"] == "auth-user-id"
    assert result["context"]["role"] == "CLIENTE"
    assert result["context"]["roles"] == "CLIENTE"
    assert result["context"]["permissions"] == "ordem-servico:read"


def test_authorizer_denies_missing_token() -> None:
    result = handler.lambda_handler({"headers": {}}, None)

    assert result == {"isAuthorized": False, "context": {}}


def test_authorizer_accepts_lowercase_bearer(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "customer_id": "customer-id",
            "cpf": "12345678909",
            "role": "CLIENTE",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {"headers": {"authorization": "bearer valid-token"}},
        None,
    )

    assert result["isAuthorized"] is True
