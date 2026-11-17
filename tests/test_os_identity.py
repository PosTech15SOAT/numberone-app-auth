import json
from unittest.mock import MagicMock, Mock
from urllib.error import HTTPError, URLError
from uuid import UUID

import pytest

from src.shared import os_identity

PRIVATE_ORIGIN = "http://internal-numberone-123.us-east-1.elb.amazonaws.com"


@pytest.fixture(autouse=True)
def identity_settings(monkeypatch):
    os_identity._settings.cache_clear()
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", PRIVATE_ORIGIN)
    yield
    os_identity._settings.cache_clear()


@pytest.mark.parametrize("origin", [
    PRIVATE_ORIGIN, PRIVATE_ORIGIN + "/", "http://10.0.0.10:8080",
    "http://172.16.0.10", "http://192.168.1.10",
    "http://internal-numberone-123.elb.us-east-1.amazonaws.com",
])
def test_accepts_private_http_origin(origin, monkeypatch):
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", origin)
    assert os_identity._settings() == origin.removesuffix("/")


@pytest.mark.parametrize("origin", [
    "https://10.0.0.10", "http://example.com", "http://8.8.8.8", "http://127.0.0.1",
    "http://169.254.169.254", "http://[::1]", "http://172.32.0.1", "http://localhost",
    "http://user:password@10.0.0.10", "http://10.0.0.10/path", "http://10.0.0.10//",
    "http://10.0.0.10?query=1", "http://10.0.0.10#fragment", "http://10.0.0.10?",
    "http://10.0.0.10:99999", "http://10.0.0.10:bad", "http://10.0.0.10:",
    "http://10.0.0.10\n", PRIVATE_ORIGIN + ".example.com",
    "http://public-123.us-east-1.elb.amazonaws.com",
])
def test_rejects_public_or_malformed_origin(origin, monkeypatch):
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", origin)
    with pytest.raises((RuntimeError, ValueError)):
        os_identity._settings()


def test_posts_identity_without_service_credentials(monkeypatch):
    reply = Mock(status=204)
    opener = MagicMock()
    opener.open.return_value.__enter__.return_value = reply
    build_opener = Mock(return_value=opener)
    monkeypatch.setattr(os_identity, "build_opener", build_opener)

    assert os_identity.matches_active_customer("customer-id", "52998224725")
    (request,), kwargs = opener.open.call_args
    assert request.full_url == PRIVATE_ORIGIN + "/internal/auth/customer-identity"
    assert request.method == "POST"
    assert json.loads(request.data) == {"customerId": "customer-id", "cpf": "52998224725"}
    assert request.get_header("Content-type") == "application/json"
    assert UUID(request.get_header("X-correlation-id"))
    assert request.get_header("Authorization") is None
    assert kwargs == {"timeout": 2}
    proxy_handler, redirect_handler = build_opener.call_args.args
    assert proxy_handler.proxies == {}
    assert redirect_handler.redirect_request(None, None, 302, "", {}, "http://evil") is None


@pytest.mark.parametrize("status", [200, 201, 202])
def test_only_204_confirms_identity(status, monkeypatch):
    opener = MagicMock()
    opener.open.return_value.__enter__.return_value = Mock(status=status)
    monkeypatch.setattr(os_identity, "build_opener", lambda *args: opener)
    assert not os_identity.matches_active_customer("customer-id", "52998224725")


@pytest.mark.parametrize("status", [301, 302, 307, 308, 400, 401, 403, 404, 500, 503])
def test_http_errors_fail_closed(status, monkeypatch):
    opener = MagicMock()
    opener.open.side_effect = HTTPError(PRIVATE_ORIGIN, status, "failure", {}, None)
    monkeypatch.setattr(os_identity, "build_opener", lambda *args: opener)
    if status == 404:
        assert not os_identity.matches_active_customer("customer-id", "52998224725")
    else:
        with pytest.raises(HTTPError):
            os_identity.matches_active_customer("customer-id", "52998224725")


@pytest.mark.parametrize("error", [TimeoutError(), URLError("unavailable")])
def test_transport_errors_propagate(error, monkeypatch):
    opener = MagicMock()
    opener.open.side_effect = error
    monkeypatch.setattr(os_identity, "build_opener", lambda *args: opener)
    with pytest.raises(type(error)):
        os_identity.matches_active_customer("customer-id", "52998224725")
