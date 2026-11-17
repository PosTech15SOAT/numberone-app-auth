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


@pytest.fixture
def os_service(monkeypatch):
    """Exercise urllib against a local OS stub using the provisioned private origin."""
    import json
    import socket
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    from src.shared import os_identity

    state = {"active": True, "cpf": "52998224725", "status": None, "requests": []}

    class IdentityHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append((self.path, dict(self.headers), body))
            matches = state["active"] and body == {
                "customerId": state["customer_id"], "cpf": state["cpf"],
            }
            self.send_response(state["status"] or (204 if matches else 404))
            self.send_header("Location", "http://10.0.0.10/redirected")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), IdentityHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connect = socket.create_connection

    def private_connection(address, *args, **kwargs):
        assert address == ("10.0.0.10", 80)
        return connect(server.server_address, *args, **kwargs)

    monkeypatch.setattr(socket, "create_connection", private_connection)
    monkeypatch.setenv("OS_IDENTITY_BASE_URL", "http://10.0.0.10")
    os_identity._settings.cache_clear()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        os_identity._settings.cache_clear()
