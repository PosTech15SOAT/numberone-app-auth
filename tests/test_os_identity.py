from unittest.mock import Mock

from src.shared import os_identity


def test_identity_client_loads_the_private_ca(monkeypatch):
    token = "s" * 32
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", "https://internal-identity.example")
    monkeypatch.setenv("OS_IDENTITY_SECRET_ARN", "identity-credential")
    credentials = {"token": token, "ca_pem": "private-ca"}
    monkeypatch.setattr(os_identity, "_read_secret", lambda _: credentials)
    ssl_context = Mock()
    create_context = Mock(return_value=ssl_context)
    monkeypatch.setattr(os_identity.ssl, "create_default_context", create_context)

    os_identity._settings.cache_clear()
    try:
        assert os_identity._settings() == ("https://internal-identity.example", token, ssl_context)
        create_context.assert_called_once_with(cadata="private-ca")
    finally:
        os_identity._settings.cache_clear()
