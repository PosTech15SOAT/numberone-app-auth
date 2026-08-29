from src.shared import config
from src.shared.jwt_service import issue_token, validate_token


def test_issue_and_validate_token(monkeypatch) -> None:
    config.jwt_settings.cache_clear()
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-at-least-32-characters")
    monkeypatch.setenv("JWT_ISSUER", "numberone-auth-test")
    monkeypatch.setenv("JWT_AUDIENCE", "numberone-api-test")
    monkeypatch.setenv("JWT_EXPIRATION_SECONDS", "3600")

    token, expires_in = issue_token(
        subject="auth-user-id",
        customer_id="customer-id",
        cpf="12345678909",
        roles=["CUSTOMER"],
        permissions=["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"],
    )
    claims = validate_token(token)

    assert expires_in == 3600
    assert claims["sub"] == "auth-user-id"
    assert claims["customer_id"] == "customer-id"
    assert claims["role"] == "CUSTOMER"
    assert claims["roles"] == ["CUSTOMER"]
    assert claims["permissions"] == ["SERVICE_ORDER_TRACK_OWN", "BUDGET_RESPOND_OWN"]
    assert claims["status"] == "ACTIVE"

    config.jwt_settings.cache_clear()
