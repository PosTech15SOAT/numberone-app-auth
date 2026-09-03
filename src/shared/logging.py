import json
import logging
from typing import Any


def log_json(logger: logging.Logger, level: int, message: str, **attributes: Any) -> None:
    payload = {
        "message": message,
        **attributes,
    }
    logger.log(level, json.dumps(payload, default=str, ensure_ascii=False))


def mask_cpf(cpf: str) -> str:
    if len(cpf) != 11:
        return "***"
    return f"{cpf[:3]}.***.***-{cpf[-2:]}"
