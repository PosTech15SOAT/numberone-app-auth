import logging
from typing import Any

import jwt

from src.shared.jwt_service import validate_token
from src.shared.logging import log_json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_id = _request_id(event, context)
    token = _extract_bearer_token(event)

    if not token:
        log_json(logger, logging.INFO, "authorizer_missing_token", requestId=request_id)
        return _deny()

    try:
        claims = validate_token(token)
        log_json(
            logger,
            logging.INFO,
            "authorizer_allow",
            requestId=request_id,
            principalId=str(claims.get("sub", "")),
            customerId=str(claims.get("customer_id", "")),
        )
        return {
            "isAuthorized": True,
            "context": {
                "principalId": str(claims.get("sub", "")),
                "customerId": str(claims.get("customer_id", "")),
                "cpf": str(claims.get("cpf", "")),
                "role": str(claims.get("role", "")),
                "roles": ",".join(claims.get("roles", [])),
                "permissions": ",".join(claims.get("permissions", [])),
            },
        }
    except jwt.PyJWTError:
        log_json(logger, logging.INFO, "authorizer_reject_invalid_jwt", requestId=request_id)
        return _deny()
    except Exception:
        log_json(logger, logging.ERROR, "authorizer_unexpected_error", requestId=request_id)
        logger.exception("Authorizer failed unexpectedly.")
        return _deny()


def _extract_bearer_token(event: dict[str, Any]) -> str | None:
    headers = event.get("headers") or {}
    authorization = headers.get("authorization") or headers.get("Authorization") or ""

    if not authorization.lower().startswith("bearer "):
        return None

    return authorization.split(" ", 1)[1].strip()


def _deny() -> dict[str, Any]:
    return {
        "isAuthorized": False,
        "context": {},
    }


def _request_id(event: dict[str, Any], context: Any) -> str:
    request_context = event.get("requestContext") or {}
    return (
        request_context.get("requestId")
        or getattr(context, "aws_request_id", None)
        or "local"
    )
