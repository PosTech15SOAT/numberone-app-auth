import json
from typing import Any


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def bad_request(message: str) -> dict[str, Any]:
    return response(400, {"message": message})


def unauthorized(message: str = "Unauthorized") -> dict[str, Any]:
    return response(401, {"message": message})


def not_found(message: str) -> dict[str, Any]:
    return response(404, {"message": message})


def server_error(message: str = "Internal server error") -> dict[str, Any]:
    return response(500, {"message": message})
