import json
import os
import re
from functools import lru_cache
from ipaddress import ip_address, ip_network
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _is_private_host(host: str) -> bool:
    # Cloud publishes an internal AWS load balancer or an RFC1918 address.
    if re.fullmatch(
        r"internal-[a-z0-9-]+\.(?:[a-z0-9-]+\.elb|elb\.[a-z0-9-]+)"
        r"\.amazonaws\.com(?:\.cn)?", host
    ):
        return True
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return any(address in ip_network(network) for network in (
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    ))


@lru_cache(maxsize=1)
def _settings() -> str:
    base_url = os.environ["OS_IDENTITY_BASE_URL"].removesuffix("/")
    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "http"
        or not parsed.hostname or not _is_private_host(parsed.hostname)
        or parsed.username is not None or parsed.password is not None
        or parsed.query or parsed.fragment or parsed.path
        or "?" in base_url or "#" in base_url
        or any(character.isspace() or ord(character) < 32 for character in base_url)
    ):
        raise RuntimeError("Invalid private OS identity base URL.")
    # Accessing port also rejects malformed or out-of-range ports.
    if parsed.port is None and parsed.netloc.endswith(":"):
        raise RuntimeError("Invalid private OS identity port.")
    return base_url


def matches_active_customer(customer_id: str, cpf: str) -> bool:
    base_url = _settings()
    request = Request(
        f"{base_url}/internal/auth/customer-identity",
        data=json.dumps({"customerId": customer_id, "cpf": cpf}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Correlation-Id": str(uuid4()),
        },
        method="POST",
    )
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=2) as reply:
            return reply.status == 204
    except HTTPError as exception:
        if exception.code == 404:
            return False
        raise
