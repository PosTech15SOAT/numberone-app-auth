import re
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.shared.config import jwt_settings
from src.shared.cpf import is_valid_cpf
from src.shared.identity import ADMIN, CUSTOMER, canonical_uuid

_PERMISSION = re.compile(r"[A-Za-z][A-Za-z0-9_:.-]{0,119}")


def issue_token(
    *,
    subject: str,
    customer_id: str | None,
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
        "role": roles[0],
        "roles": roles,
        "permissions": permissions,
        "status": "ACTIVE",
        "iss": settings["issuer"],
        "aud": settings["audience"],
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(payload, settings["secret"], algorithm="HS256"), expires_in


def validate_token(token: str) -> dict[str, Any]:
    settings = jwt_settings()
    claims = jwt.decode(
        token,
        settings["secret"],
        algorithms=["HS256"],
        issuer=settings["issuer"],
        audience=settings["audience"],
        options={"require": ["sub", "cpf", "role", "roles", "permissions", "status", "iat", "exp"]},
    )
    role = claims["role"]
    cpf = claims["cpf"]
    permissions = claims["permissions"]
    issued_at, expires_at = claims["iat"], claims["exp"]
    if (
        not canonical_uuid(claims["sub"])
        or role not in (ADMIN, CUSTOMER)
        or claims["roles"] != [role]
        or "customer_id" not in claims
        or (role == CUSTOMER and not canonical_uuid(claims["customer_id"]))
        or (role == ADMIN and claims["customer_id"] is not None)
        or not isinstance(cpf, str) or not re.fullmatch(r"[0-9]{11}", cpf) or not is_valid_cpf(cpf)
        or claims["status"] != "ACTIVE"
        or not isinstance(permissions, list)
        or any(not isinstance(key, str) or not _PERMISSION.fullmatch(key) for key in permissions)
        or len(set(permissions)) != len(permissions)
        or type(issued_at) is not int or type(expires_at) is not int
        or expires_at <= issued_at
    ):
        raise jwt.InvalidTokenError("Invalid identity claims.")
    return claims
