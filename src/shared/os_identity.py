import json
import os
import ssl
from functools import lru_cache
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from uuid import uuid4

from src.shared.config import _read_secret


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@lru_cache(maxsize=1)
def _settings() -> tuple[str, str, ssl.SSLContext]:
    base_url = os.environ["OS_IDENTITY_BASE_URL"].rstrip("/")
    parsed = urlsplit(base_url)
    secret_arn = os.getenv("OS_IDENTITY_SECRET_ARN")
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname or parsed.username or parsed.password
        or parsed.query or parsed.fragment or parsed.path
        or (secret_arn and parsed.scheme != "https")
    ):
        raise RuntimeError("Invalid OS identity base URL.")
    credentials = (
        _read_secret(secret_arn) if secret_arn else {"token": os.getenv("OS_IDENTITY_TOKEN")}
    )
    token = credentials.get("token")
    if not isinstance(token, str) or len(token) < 32:
        raise RuntimeError("OS identity credential not configured.")
    return base_url, token, ssl.create_default_context(cadata=credentials.get("ca_pem"))


def matches_active_customer(customer_id: str, cpf: str) -> bool:
    base_url, token, tls_context = _settings()
    request = Request(
        f"{base_url}/internal/auth/customer-identity",
        data=json.dumps({"customerId": customer_id, "cpf": cpf}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Correlation-Id": str(uuid4()),
        },
        method="POST",
    )
    opener = build_opener(_NoRedirect(), HTTPSHandler(context=tls_context))
    try:
        with opener.open(request, timeout=2) as reply:
            return reply.status == 204
    except HTTPError as exception:
        if exception.code == 404:
            return False
        raise
