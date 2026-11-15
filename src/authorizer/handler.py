import logging
from typing import Any

import jwt

from src.shared.correlation import MissingCorrelationIdError, resolve_correlation_id
from src.shared.db import find_token_identity
from src.shared.identity import ADMIN, ADMIN_ACCESS, TRACK_OWN, TRACKING_ROUTES, customer_id
from src.shared.jwt_service import validate_token
from src.shared.logging import log_json
from src.shared.os_identity import matches_active_customer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        correlation_id = resolve_correlation_id(event)
    except MissingCorrelationIdError:
        correlation_id = None

    token = _extract_bearer_token(event)
    if not token:
        return {"errorMessage": "Unauthorized"}

    try:
        claims = validate_token(token)
    except (jwt.PyJWTError, TypeError, ValueError):
        return {"errorMessage": "Unauthorized"}
    except Exception as exception:
        return _dependency_error(event, context, correlation_id, exception)

    try:
        identity = find_token_identity(claims["sub"])
        if (
            identity is None
            or claims["cpf"] != identity["cpf"]
            or claims["role"] != identity["perfil"]
            or claims["customer_id"] != customer_id(identity)
            or set(claims["permissions"]) != set(identity["permissions"])
        ):
            return {"errorMessage": "Unauthorized"}

        route_key = event.get("routeKey") or ""
        permissions = set(identity["permissions"])
        is_admin = identity["perfil"] == ADMIN and ADMIN_ACCESS in permissions
        is_tracking = route_key in TRACKING_ROUTES
        if not (is_admin and (_is_admin_route(route_key) or is_tracking)) and not (
            is_tracking and claims["customer_id"] and TRACK_OWN in permissions
        ):
            return {"isAuthorized": False, "context": {}}

        if claims["customer_id"] and not matches_active_customer(
            claims["customer_id"], claims["cpf"]
        ):
            return {"errorMessage": "Unauthorized"}

        authorizer_context = {
            "principalId": claims["sub"],
            "customerId": claims["customer_id"] or "",
            "role": claims["role"],
            "roles": ",".join(claims["roles"]),
            "permissions": ",".join(claims["permissions"]),
            "userStatus": claims["status"],
        }
        if correlation_id is not None:
            authorizer_context["correlationId"] = correlation_id
        return {"isAuthorized": True, "context": authorizer_context}
    except Exception as exception:
        return _dependency_error(event, context, correlation_id, exception)


def _is_admin_route(route_key: str) -> bool:
    method, _, path = route_key.partition(" ")
    return method in {"GET", "POST", "PUT", "PATCH", "DELETE"} and path.startswith("/api/admin/")


def _extract_bearer_token(event: dict[str, Any]) -> str | None:
    headers = event.get("headers") or {}
    authorization = next(
        (value for name, value in headers.items() if name.lower() == "authorization"), ""
    )
    if not isinstance(authorization, str) or "," in authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else None


def _dependency_error(event, context, correlation_id, exception) -> dict[str, Any]:
    request_id = (event.get("requestContext") or {}).get("requestId") or getattr(
        context, "aws_request_id", None
    )
    log_json(logger, logging.ERROR, "authorizer_dependency_error", requestId=request_id,
             correlation_id=correlation_id, errorType=type(exception).__name__)
    raise RuntimeError("Authorization dependency unavailable.") from None
