import json
import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def jwt_settings() -> dict[str, Any]:
    secret = os.getenv("JWT_SECRET")
    secret_arn = os.getenv("JWT_SECRET_ARN")

    if secret_arn:
        secret_payload = _read_secret(secret_arn)
        secret = secret_payload.get("secret") or secret_payload.get("JWT_SECRET")

    if not secret:
        raise RuntimeError("JWT secret not configured.")

    return {
        "secret": secret,
        "issuer": os.getenv("JWT_ISSUER", "numberone-auth"),
        "audience": os.getenv("JWT_AUDIENCE", "numberone-api"),
        "expiration_seconds": int(os.getenv("JWT_EXPIRATION_SECONDS", "3600")),
    }


@lru_cache(maxsize=1)
def db_settings() -> dict[str, Any]:
    secret_arn = os.getenv("DB_SECRET_ARN")

    if secret_arn:
        secret_payload = _read_secret(secret_arn)
        settings = {
            "host": secret_payload.get("host"),
            "port": int(secret_payload.get("port", 5432)),
            "dbname": (
                secret_payload.get("dbname")
                or secret_payload.get("database")
                or secret_payload.get("DB_NAME")
            ),
            "username": secret_payload.get("username") or secret_payload.get("user"),
            "password": secret_payload.get("password"),
        }
        _require_settings(settings, ["host", "dbname", "username", "password"])
        return settings

    required = ["DB_HOST", "DB_NAME", "DB_USERNAME", "DB_PASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing database settings: {', '.join(missing)}")

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.environ["DB_NAME"],
        "username": os.environ["DB_USERNAME"],
        "password": os.environ["DB_PASSWORD"],
    }


def _read_secret(secret_arn: str) -> dict[str, Any]:
    import boto3

    client = boto3.client("secretsmanager")
    result = client.get_secret_value(SecretId=secret_arn)
    secret_string = result["SecretString"]

    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        return {"secret": secret_string}


def _require_settings(settings: dict[str, Any], names: list[str]) -> None:
    missing = [name for name in names if not settings.get(name)]
    if missing:
        raise RuntimeError(f"Missing secret settings: {', '.join(missing)}")
