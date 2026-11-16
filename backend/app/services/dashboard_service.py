from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.uploaded_dataset import UploadedDataset
from app.models.network_event import NetworkEvent
from app.models.prediction import Prediction
from app.models.factory import Factory


def get_dashboard_statistics(
    db: Session,
    company_id: int | None = None,
    hours: int | None = None
):
    """
    Retrieve dashboard statistics.

    company_id=None means platform-wide statistics.
    hours=None means all-time statistics.
    """

    cutoff = None

    if hours is not None and hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # 1. Uploaded datasets
    datasets_query = db.query(UploadedDataset)

    if company_id is not None:
        datasets_query = datasets_query.filter(
            UploadedDataset.company_id == company_id
        )

    if cutoff is not None:
        datasets_query = datasets_query.filter(
            UploadedDataset.created_at >= cutoff
        )

    total_datasets = datasets_query.with_entities(
        func.count(UploadedDataset.id)
    ).scalar() or 0

    total_records = datasets_query.with_entities(
        func.coalesce(func.sum(UploadedDataset.records_count), 0)
    ).scalar() or 0

    # 2. Network events
    events_query = db.query(NetworkEvent)

    if company_id is not None:
        events_query = events_query.filter(
            NetworkEvent.company_id == company_id
        )

    if cutoff is not None:
        event_timestamp = func.coalesce(
            NetworkEvent.event_time,
            NetworkEvent.created_at
        )
        events_query = events_query.filter(
            event_timestamp >= cutoff
        )

    total_network_events = events_query.with_entities(
        func.count(NetworkEvent.id)
    ).scalar() or 0

    # 3. AI predictions
    predictions_query = db.query(Prediction)

    if company_id is not None:
        predictions_query = predictions_query.filter(
            Prediction.company_id == company_id
        )

    if cutoff is not None:
        predictions_query = predictions_query.filter(
            Prediction.created_at >= cutoff
        )

    total_predictions = predictions_query.with_entities(
        func.count(Prediction.id)
    ).scalar() or 0

    # 4. Datasets grouped by type
    dataset_rows = datasets_query.with_entities(
        UploadedDataset.dataset_type,
        func.count(UploadedDataset.id),
        func.coalesce(func.sum(UploadedDataset.records_count), 0)
    ).group_by(
        UploadedDataset.dataset_type
    ).all()

    datasets_by_type = [
        {
            "dataset_type": row[0],
            "files_count": row[1],
            "records_count": row[2]
        }
        for row in dataset_rows
    ]

    # 5. Predictions grouped by label
    prediction_rows = predictions_query.with_entities(
        Prediction.prediction_label,
        func.count(Prediction.id)
    ).group_by(
        Prediction.prediction_label
    ).all()

    predictions_by_label = [
        {
            "prediction_label": row[0] or "Unclassified",
            "count": row[1]
        }
        for row in prediction_rows
    ]

    # 6. Statistics for active factories
    factories_query = db.query(Factory).filter(
        Factory.is_active.is_(True)
    )

    if company_id is not None:
        factories_query = factories_query.filter(
            Factory.company_id == company_id
        )

    factories = factories_query.all()
    factory_statistics = []

    for factory in factories:
        factory_datasets = db.query(UploadedDataset).filter(
            UploadedDataset.factory_id == factory.id
        )

        factory_predictions = db.query(Prediction).filter(
            Prediction.factory_id == factory.id
        )

        if company_id is not None:
            factory_datasets = factory_datasets.filter(
                UploadedDataset.company_id == company_id
            )
            factory_predictions = factory_predictions.filter(
                Prediction.company_id == company_id
            )

        if cutoff is not None:
            factory_datasets = factory_datasets.filter(
                UploadedDataset.created_at >= cutoff
            )
            factory_predictions = factory_predictions.filter(
                Prediction.created_at >= cutoff
            )

        datasets_count = factory_datasets.with_entities(
            func.count(UploadedDataset.id)
        ).scalar() or 0

        records_count = factory_datasets.with_entities(
            func.coalesce(func.sum(UploadedDataset.records_count), 0)
        ).scalar() or 0

        predictions_count = factory_predictions.with_entities(
            func.count(Prediction.id)
        ).scalar() or 0

        factory_statistics.append({
            "factory_id": factory.id,
            "factory_name": factory.name,
            "datasets_count": datasets_count,
            "records_count": records_count,
            "predictions_count": predictions_count
        })

    return {
        "total_datasets": total_datasets,
        "total_records": total_records,
        "total_network_events": total_network_events,
        "total_predictions": total_predictions,
        "datasets_by_type": datasets_by_type,
        "predictions_by_label": predictions_by_label,
        "factories": factory_statistics
    }
