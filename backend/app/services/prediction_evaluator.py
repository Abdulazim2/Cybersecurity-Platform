def evaluate_prediction_severity(prediction):
    """
    Evaluate a prediction and return its notification severity.
    Returns None when no security alert should be generated.
    """

    label = (
        prediction.prediction_label or ""
    ).strip().lower()

    output = prediction.prediction_output or {}

    status = ""

    if isinstance(output, dict):
        status = str(
            output.get("status", "")
        ).strip().lower()

    threat_values = {
        "malicious",
        "attack",
        "intrusion",
        "threat",
        "critical"
    }

    suspicious_values = {
        "suspicious",
        "anomaly",
        "abnormal"
    }

    if label in threat_values or status in threat_values:
        return "critical"

    if label in suspicious_values or status in suspicious_values:
        return "warning"

    return None
