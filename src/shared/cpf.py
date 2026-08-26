import re


def only_digits(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\D", "", value)


def is_valid_cpf(value: str | None) -> bool:
    cpf = only_digits(value)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    first_digit = _calculate_digit(cpf[:9], 10)
    second_digit = _calculate_digit(cpf[:10], 11)

    return first_digit == int(cpf[9]) and second_digit == int(cpf[10])


def _calculate_digit(base: str, initial_weight: int) -> int:
    total = 0
    weight = initial_weight

    for digit in base:
        total += int(digit) * weight
        weight -= 1

    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder
