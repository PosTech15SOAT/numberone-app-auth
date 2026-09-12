import pytest

from src.shared.correlation import HEADER_NAME, MissingCorrelationIdError, resolve_correlation_id


def test_resolve_correlation_id_preserves_valid_header() -> None:
    correlation_id = resolve_correlation_id({"headers": {HEADER_NAME: "teste-numberone-123"}})

    assert correlation_id == "teste-numberone-123"


def test_resolve_correlation_id_reads_header_case_insensitively() -> None:
    assert resolve_correlation_id({"headers": {"x-correlation-id": "lower"}}) == "lower"
    assert resolve_correlation_id({"headers": {"X-Correlation-Id": "mixed"}}) == "mixed"
    assert resolve_correlation_id({"headers": {"X-CORRELATION-ID": "upper"}}) == "upper"


def test_resolve_correlation_id_requires_header() -> None:
    with pytest.raises(MissingCorrelationIdError):
        resolve_correlation_id({"headers": {}})


def test_resolve_correlation_id_requires_non_blank_header() -> None:
    with pytest.raises(MissingCorrelationIdError):
        resolve_correlation_id({"headers": {HEADER_NAME: " "}})


def test_resolve_correlation_id_accepts_arbitrary_non_uuid_value() -> None:
    correlation_id = resolve_correlation_id({"headers": {HEADER_NAME: "teste-julio-os-001"}})

    assert correlation_id == "teste-julio-os-001"
