from types import SimpleNamespace

import pytest

from app.services.prediction_evaluator import evaluate_prediction_severity


@pytest.mark.parametrize(
    "label, output, expected",
    [
        ("malicious", None, "critical"),
        ("attack", None, "critical"),
        (None, {"status": "threat"}, "critical"),
        (" CRITICAL ", None, "critical"),
        ("suspicious", None, "warning"),
        (None, {"status": "anomaly"}, "warning"),
        ("normal", {"status": "normal"}, None),
        (None, {}, None),
        (None, ["malicious"], None),
    ],
)
def test_prediction_severity(label, output, expected):
    prediction = SimpleNamespace(
        prediction_label=label,
        prediction_output=output
    )

    result = evaluate_prediction_severity(prediction)

    assert result == expected
