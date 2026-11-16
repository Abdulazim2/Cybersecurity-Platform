import pytest

from app.services.data_ingestion_service import normalize_float


@pytest.mark.parametrize(
    "value",
    ["nan", "inf", "-inf"]
)
def test_normalize_float_rejects_non_finite_values(value):
    with pytest.raises(ValueError):
        normalize_float(value, "test_field", 1)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("12.5", 12.5),
        ("0", 0.0),
        ("100", 100.0),
    ]
)
def test_normalize_float_accepts_valid_values(value, expected):
    result = normalize_float(value, "test_field", 1)
    assert result == expected


def test_normalize_float_rejects_negative_values():
    with pytest.raises(ValueError):
        normalize_float("-12.5", "test_field", 1)


def test_normalize_float_rejects_boolean_values():
    with pytest.raises(ValueError):
        normalize_float(True, "test_field", 1)
