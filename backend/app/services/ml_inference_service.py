class MLModelNotConfiguredError(RuntimeError):
    """Raised when the ML model is not available for inference."""


def get_ml_pipeline_status() -> dict:
    """Return the current ML pipeline readiness status."""
    return {
        "status": "not_configured",
        "model_loaded": False,
        "message": "The ML model has not been integrated yet."
    }


def run_inference(records: list[dict]) -> list[dict]:
    """
    Run model inference on prepared records.

    This function will be implemented after the ML team provides
    the trained model and its preprocessing/inference contract.
    """
    raise MLModelNotConfiguredError(
        "ML inference is unavailable because no trained model is configured."
    )
