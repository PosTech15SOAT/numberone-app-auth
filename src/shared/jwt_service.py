from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.shared.config import jwt_settings


def issue_token(
    *,
    subject: str,
    customer_id: str,
    cpf: str,
    roles: list[str],
    permissions: list[str],
) -> tuple[str, int]:
    settings = jwt_settings()
    expires_in = settings["expiration_seconds"]
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=expires_in)

    payload = {
        "sub": subject,
        "customer_id": customer_id,
        "cpf": cpf,
        "role": roles[0] if roles else "CLIENTE",
        "roles": roles,
        "permissions": permissions,
        "iss": settings["issuer"],
        "aud": settings["audience"],
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, settings["secret"], algorithm="HS256")
    return token, expires_in


def validate_token(token: str) -> dict[str, Any]:
    settings = jwt_settings()
    return jwt.decode(
        token,
        settings["secret"],
        algorithms=["HS256"],
        issuer=settings["issuer"],
        audience=settings["audience"],
    )
