from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes

ITERATIONS = 600_000
DUMMY_HASH = "0" * 32 + ":" + "0" * 64


def valid_password(password: object) -> bool:
    return isinstance(password, str) and 12 <= len(password) <= 128


def hash_password(password: str) -> str:
    if not valid_password(password):
        raise ValueError("A senha deve ter entre 12 e 128 caracteres.")
    salt = token_bytes(16)
    return f"{salt.hex()}:{_digest(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split(":")
    return compare_digest(_digest(password, bytes.fromhex(salt)), bytes.fromhex(expected))


def _digest(password: str, salt: bytes) -> bytes:
    return pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
