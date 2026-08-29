from src.authorizer import handler


def test_authorizer_allows_valid_bearer_token(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "customer_id": "customer-id",
            "cpf": "12345678909",
            "role": "CUSTOMER",
            "roles": ["CUSTOMER"],
            "permissions": ["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"],
            "status": "ACTIVE",
        },
    )

    result = handler.lambda_handler(
        {"headers": {"Authorization": "Bearer valid-token"}},
        None,
    )

    assert result["isAuthorized"] is True
    assert result["context"]["principalId"] == "auth-user-id"
    assert result["context"]["role"] == "CUSTOMER"
    assert result["context"]["roles"] == "CUSTOMER"
    assert result["context"]["permissions"] == "SERVICE_ORDER_TRACK_OWN,BUDGET_RESPOND_OWN"
    assert result["context"]["status"] == "ACTIVE"
    assert result["context"]["correlationId"] == "local"


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
            "role": "CUSTOMER",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {"headers": {"authorization": "bearer valid-token"}},
        None,
    )

    assert result["isAuthorized"] is True
