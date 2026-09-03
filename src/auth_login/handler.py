import json
import logging
from json import JSONDecodeError
from typing import Any

from src.shared.cpf import is_valid_cpf, only_digits
from src.shared.db import find_active_customer_by_cpf, find_or_create_auth_user, find_rbac_claims
from src.shared.http import bad_request, not_found, response, server_error, unauthorized
from src.shared.jwt_service import issue_token
from src.shared.logging import log_json, mask_cpf

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_id = _request_id(event, context)

    try:
        body = _parse_body(event)
        cpf = only_digits(body.get("cpf"))

        if not is_valid_cpf(cpf):
            log_json(logger, logging.INFO, "auth_login_invalid_cpf", requestId=request_id)
            return bad_request("CPF invalido.")

        customer = find_active_customer_by_cpf(cpf)
        if not customer:
            log_json(
                logger,
                logging.INFO,
                "auth_login_customer_not_found",
                requestId=request_id,
                cpf=mask_cpf(cpf),
            )
            return not_found("Cliente nao encontrado.")

        if customer.get("ativo") is not True:
            log_json(
                logger,
                logging.INFO,
                "auth_login_inactive_customer",
                requestId=request_id,
                customerId=str(customer.get("id")),
            )
            return unauthorized("Cliente inativo.")

        auth_user = find_or_create_auth_user(customer, cpf)
        if auth_user.get("ativo") is not True:
            log_json(
                logger,
                logging.INFO,
                "auth_login_inactive_auth_user",
                requestId=request_id,
                authUserId=str(auth_user.get("id")),
            )
            return unauthorized("Usuario de autenticacao inativo.")

        claims = find_rbac_claims(str(auth_user["id"]))
        token, expires_in = issue_token(
            subject=str(auth_user["id"]),
            customer_id=str(customer["id"]),
            cpf=cpf,
            roles=claims["roles"],
            permissions=claims["permissions"],
        )

        log_json(
            logger,
            logging.INFO,
            "auth_login_success",
            requestId=request_id,
            authUserId=str(auth_user["id"]),
            customerId=str(customer["id"]),
            roles=claims["roles"],
            permissionsCount=len(claims["permissions"]),
        )

        return response(
            200,
            {
                "accessToken": token,
                "tokenType": "Bearer",
                "expiresIn": expires_in,
            },
        )
    except (JSONDecodeError, ValueError):
        log_json(logger, logging.INFO, "auth_login_invalid_request", requestId=request_id)
        return bad_request("Request invalido.")
    except Exception:
        log_json(logger, logging.ERROR, "auth_login_unexpected_error", requestId=request_id)
        logger.exception("Authentication failed unexpectedly.")
        return server_error()


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body") or "{}"

    if event.get("isBase64Encoded"):
        raise ValueError("Base64 body is not supported.")

    return json.loads(raw_body)


def _request_id(event: dict[str, Any], context: Any) -> str:
    request_context = event.get("requestContext") or {}
    return (
        request_context.get("requestId")
        or getattr(context, "aws_request_id", None)
        or "local"
    )
