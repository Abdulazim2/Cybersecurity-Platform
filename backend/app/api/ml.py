from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, is_super_admin
from app.models.user import User
from app.models.uploaded_dataset import UploadedDataset
from app.services.ml_inference_service import (
    get_ml_pipeline_status,
    run_inference,
    MLModelNotConfiguredError
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class MLPredictionRequest(BaseModel):
    dataset_id: int = Field(gt=0)
    record_index: int = Field(ge=0)


@router.get("/status")
def get_ml_status():
    return get_ml_pipeline_status()


@router.post("/predict")
def predict_dataset_record(
    request: MLPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    # Find the dataset within the user's allowed company scope.
    query = db.query(UploadedDataset).filter(
        UploadedDataset.id == request.dataset_id
    )

    if not is_super_admin(current_user, db):
        query = query.filter(
            UploadedDataset.company_id == current_user.company_id
        )

    dataset = query.first()

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Validate the requested record.
    if not isinstance(dataset.records, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset records are not available in the expected format"
        )

    if request.record_index >= len(dataset.records):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Record index is outside the dataset range"
        )

    record = dataset.records[request.record_index]

    if not isinstance(record, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected dataset record has an invalid format"
        )

    # Run inference only through the trusted backend service.
    try:
        results = run_inference([record])

    except MLModelNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model is not configured yet"
        )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ML inference returned no results"
        )

    return {
        "dataset_id": dataset.id,
        "record_index": request.record_index,
        "result": results[0]
    }
