import pytest

from src.shared import config


@pytest.fixture
def signing(monkeypatch):
    config.jwt_settings.cache_clear()
    monkeypatch.delenv("JWT_SECRET_ARN", raising=False)
    monkeypatch.setenv("JWT_SECRET", "synthetic-numberone-identity-signing-key")
    monkeypatch.setenv("JWT_ISSUER", "numberone-auth-test")
    monkeypatch.setenv("JWT_AUDIENCE", "numberone-api-test")
    monkeypatch.setenv("JWT_EXPIRATION_SECONDS", "900")
    yield config.jwt_settings()
    config.jwt_settings.cache_clear()
