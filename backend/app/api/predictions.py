from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, is_super_admin

from app.models.user import User
from app.models.uploaded_dataset import UploadedDataset
from app.models.prediction import Prediction

from app.schemas.prediction import (
    PredictionCreate,
    PredictionResponse
)

from app.services.notification_service import create_company_notification
from app.services.prediction_evaluator import evaluate_prediction_severity


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


def get_target_dataset(
    dataset_id: int,
    db: Session,
    current_user: User
):
    """
    Super Admin can access datasets from all companies.
    Other users can access datasets from their own company only.
    """

    query = db.query(UploadedDataset).filter(
        UploadedDataset.id == dataset_id
    )

    if not is_super_admin(current_user, db):
        query = query.filter(
            UploadedDataset.company_id == current_user.company_id
        )

    dataset = query.first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    return dataset


@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_prediction(
    prediction_data: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    # Get the dataset according to the user's permissions.
    dataset = get_target_dataset(
        dataset_id=prediction_data.uploaded_dataset_id,
        db=db,
        current_user=current_user
    )

    if (
        prediction_data.record_index is not None
        and prediction_data.record_index >= dataset.records_count
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Record index is outside the dataset range"
        )

    # The company and factory must come from the dataset itself.
    new_prediction = Prediction(
        **prediction_data.model_dump(
            exclude={"uploaded_dataset_id"}
        ),
        company_id=dataset.company_id,
        factory_id=dataset.factory_id,
        uploaded_dataset_id=dataset.id
    )

    try:
        # Save temporarily to obtain the prediction ID.
        db.add(new_prediction)
        db.flush()

        # Preserve the existing ML prediction evaluation logic.
        severity = evaluate_prediction_severity(new_prediction)

        # Create a notification for the dataset's actual company.
        if severity is not None:
            label = (
                new_prediction.prediction_label
                or (
                    new_prediction.prediction_output.get("status")
                    if isinstance(new_prediction.prediction_output, dict)
                    else None
                )
                or "Unknown"
            )

            if severity == "critical":
                title = "Critical Security Threat Detected"
            else:
                title = "Suspicious Activity Detected"

            message = (
                f"Security analysis detected '{label}' "
                f"at factory ID {dataset.factory_id}. "
                f"Prediction ID: {new_prediction.id}."
            )

            create_company_notification(
                db=db,
                company_id=dataset.company_id,
                title=title,
                message=message,
                notification_type=severity,
                prediction_id=new_prediction.id
            )

        # Save prediction and notification in one transaction.
        db.commit()
        db.refresh(new_prediction)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save prediction"
        )

    return new_prediction


@router.get(
    "/",
    response_model=list[PredictionResponse]
)
def get_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    query = db.query(Prediction)

    # Super Admin sees all companies.
    # Other users see their own company's predictions.
    if not is_super_admin(current_user, db):
        query = query.filter(
            Prediction.company_id == current_user.company_id
        )

    return query.order_by(
        Prediction.created_at.desc()
    ).all()


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    query = db.query(Prediction).filter(
        Prediction.id == prediction_id
    )

    # Prevent cross-company access for ordinary users.
    if not is_super_admin(current_user, db):
        query = query.filter(
            Prediction.company_id == current_user.company_id
        )

    prediction = query.first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    return prediction
