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
        {
            "headers": {
                "Authorization": "Bearer valid-token",
                "X-Correlation-Id": "client-correlation-123",
            },
            "requestContext": {"requestId": "aws-request-id"},
        },
        None,
    )

    assert result["isAuthorized"] is True
    assert result["context"]["principalId"] == "auth-user-id"
    assert result["context"]["role"] == "CUSTOMER"
    assert result["context"]["roles"] == "CUSTOMER"
    assert result["context"]["permissions"] == "SERVICE_ORDER_TRACK_OWN,BUDGET_RESPOND_OWN"
    assert result["context"]["userStatus"] == "ACTIVE"
    assert result["context"]["correlationId"] == "client-correlation-123"


def test_authorizer_denies_missing_token() -> None:
    result = handler.lambda_handler(
        {"headers": {"X-Correlation-Id": "missing-token-correlation"}}, None
    )

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
        {
            "headers": {
                "authorization": "bearer valid-token",
                "x-correlation-id": "lower-correlation",
            }
        },
        None,
    )

    assert result["isAuthorized"] is True
    assert result["context"]["correlationId"] == "lower-correlation"


def test_authorizer_does_not_generate_correlation_id_when_header_is_absent(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {
            "headers": {"Authorization": "Bearer valid-token"},
            "requestContext": {"requestId": "aws-request-id"},
        },
        None,
    )

    assert result["isAuthorized"] is True
    assert "correlationId" not in result["context"]


def test_authorizer_does_not_generate_correlation_id_when_header_is_blank(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {
            "headers": {
                "Authorization": "Bearer valid-token",
                "X-Correlation-Id": " ",
            },
            "requestContext": {"requestId": "aws-request-id"},
        },
        None,
    )

    assert result["isAuthorized"] is True
    assert "correlationId" not in result["context"]


def test_authorizer_accepts_uppercase_correlation_header(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {
            "headers": {
                "authorization": "bearer valid-token",
                "X-CORRELATION-ID": "uppercase-correlation",
            },
        },
        None,
    )

    assert result["context"]["correlationId"] == "uppercase-correlation"


def test_authorizer_does_not_replace_correlation_id_with_aws_request_id(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "validate_token",
        lambda token: {
            "sub": "auth-user-id",
            "roles": [],
            "permissions": [],
        },
    )

    result = handler.lambda_handler(
        {
            "headers": {
                "Authorization": "Bearer valid-token",
                "X-Correlation-Id": "client-correlation",
            },
            "requestContext": {"requestId": "aws-request-id"},
        },
        None,
    )

    assert result["context"]["correlationId"] == "client-correlation"
    assert result["context"]["correlationId"] != "aws-request-id"
