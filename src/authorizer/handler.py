import logging
from typing import Any

import jwt

from src.shared.correlation import MissingCorrelationIdError, resolve_correlation_id
from src.shared.jwt_service import validate_token
from src.shared.logging import log_json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    aws_request_id = _request_id(event, context)
    try:
        correlation_id = resolve_correlation_id(event)
    except MissingCorrelationIdError:
        correlation_id = None
        log_json(
            logger,
            logging.INFO,
            "authorizer_missing_correlation_id",
            requestId=aws_request_id,
        )

    token = _extract_bearer_token(event)

    if not token:
        log_authorizer_event(
            logging.INFO, "authorizer_missing_token", aws_request_id, correlation_id
        )
        return _deny()

    try:
        claims = validate_token(token)
        log_authorizer_event(
            logging.INFO,
            "authorizer_allow",
            aws_request_id,
            correlation_id,
            principalId=str(claims.get("sub", "")),
            customerId=str(claims.get("customer_id", "")),
        )
        authorizer_context = {
            "principalId": str(claims.get("sub", "")),
            "customerId": str(claims.get("customer_id", "")),
            "cpf": str(claims.get("cpf", "")),
            "role": str(claims.get("role", "")),
            "roles": ",".join(claims.get("roles", [])),
            "permissions": ",".join(claims.get("permissions", [])),
            "status": str(claims.get("status", "")),
        }
        if correlation_id is not None:
            authorizer_context["correlationId"] = correlation_id

        return {
            "isAuthorized": True,
            "context": authorizer_context,
        }
    except jwt.PyJWTError:
        log_authorizer_event(
            logging.INFO, "authorizer_reject_invalid_jwt", aws_request_id, correlation_id
        )
        return _deny()
    except Exception:
        log_authorizer_event(
            logging.ERROR, "authorizer_unexpected_error", aws_request_id, correlation_id
        )
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


def log_authorizer_event(
    level: int,
    message: str,
    aws_request_id: str,
    correlation_id: str | None,
    **attributes: Any,
) -> None:
    log_attributes = {
        "requestId": aws_request_id,
        **attributes,
    }
    if correlation_id is not None:
        log_attributes["correlation_id"] = correlation_id
    log_json(logger, level, message, **log_attributes)


def _request_id(event: dict[str, Any], context: Any) -> str:
    request_context = event.get("requestContext") or {}
    return request_context.get("requestId") or getattr(context, "aws_request_id", None) or "local"
