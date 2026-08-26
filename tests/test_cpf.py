from src.shared.cpf import is_valid_cpf, only_digits


def test_only_digits_removes_punctuation() -> None:
    assert only_digits("123.456.789-09") == "12345678909"


def test_valid_cpf() -> None:
    assert is_valid_cpf("123.456.789-09")


def test_invalid_cpf_with_repeated_digits() -> None:
    assert not is_valid_cpf("111.111.111-11")


def test_invalid_cpf_with_wrong_check_digits() -> None:
    assert not is_valid_cpf("123.456.789-00")
