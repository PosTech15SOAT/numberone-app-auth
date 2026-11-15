from typing import Any

HEADER_NAME = "X-Correlation-Id"
LOG_FIELD = "correlation_id"

MAX_LENGTH = 128


class MissingCorrelationIdError(ValueError):
    pass


def is_valid_correlation_id(value: str | None) -> bool:
    return (
        value is not None
        and not value.isspace()
        and value != ""
        and len(value) <= MAX_LENGTH
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


def get_header_case_insensitive(headers: dict[str, Any], header_name: str) -> str | None:
    expected_header = header_name.lower()
    for name, value in headers.items():
        if name.lower() == expected_header:
            if value is None:
                return None
            return str(value)
    return None


def resolve_correlation_id(event: dict[str, Any]) -> str:
    headers = event.get("headers") or {}
    incoming_correlation_id = get_header_case_insensitive(headers, HEADER_NAME)

    if is_valid_correlation_id(incoming_correlation_id):
        return incoming_correlation_id

    raise MissingCorrelationIdError(f"{HEADER_NAME} header is required")
