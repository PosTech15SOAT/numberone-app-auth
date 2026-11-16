import json
import logging
from typing import Any

from src.shared.correlation import MissingCorrelationIdError, resolve_correlation_id
from src.shared.cpf import is_valid_cpf, only_digits
from src.shared.db import find_login_identity
from src.shared.http import bad_request, response, server_error, unauthorized
from src.shared.identity import ADMIN, CUSTOMER, customer_id
from src.shared.jwt_service import issue_token
from src.shared.logging import log_json
from src.shared.os_identity import matches_active_customer
from src.shared.password import DUMMY_HASH, valid_password, verify_password

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_id = (event.get("requestContext") or {}).get("requestId") or getattr(
        context, "aws_request_id", None
    )
    try:
        correlation_id = resolve_correlation_id(event)
    except MissingCorrelationIdError as exception:
        return bad_request(str(exception))

    try:
        if event.get("isBase64Encoded"):
            return bad_request("Request invalido.")
        body = json.loads(event.get("body") or "{}")
    except (ValueError, TypeError):
        return bad_request("Request invalido.")
    if not isinstance(body, dict):
        return bad_request("Request invalido.")

    cpf = only_digits(body["cpf"]) if isinstance(body.get("cpf"), str) else ""
    if not (cpf.isascii() and is_valid_cpf(cpf)):
        return bad_request("CPF invalido.")
    identity_type = body.get("identityType", "CUSTOMER")
    if identity_type not in ("CUSTOMER", "OPERATOR"):
        return bad_request("Tipo de identidade invalido.")
    password = body.get("password")
    if not valid_password(password):
        return unauthorized("Credenciais invalidas.")

    role = ADMIN if identity_type == "OPERATOR" else CUSTOMER
    try:
        identity = find_login_identity(cpf, role)
        stored_hash = identity["senha_hash"] if identity else DUMMY_HASH
        if not verify_password(password, stored_hash) or identity is None:
            return unauthorized("Credenciais invalidas.")

        linked_customer = customer_id(identity)
        if linked_customer is not None and not matches_active_customer(linked_customer, cpf):
            return unauthorized("Credenciais invalidas.")

        token, expires_in = issue_token(
            subject=str(identity["id"]),
            customer_id=linked_customer,
            cpf=cpf,
            roles=[role],
            permissions=identity["permissions"],
        )
    except Exception as exception:
        log_json(logger, logging.ERROR, "auth_login_error", requestId=request_id,
                 correlation_id=correlation_id, errorType=type(exception).__name__)
        return server_error()

    log_json(logger, logging.INFO, "auth_login_success", requestId=request_id,
             correlation_id=correlation_id, authUserId=str(identity["id"]), role=role)
    return response(200, {"accessToken": token, "tokenType": "Bearer", "expiresIn": expires_in})
