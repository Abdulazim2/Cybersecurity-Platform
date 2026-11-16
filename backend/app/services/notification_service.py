from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_company_notification(
    db: Session,
    company_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    prediction_id: int | None = None
) -> Notification:
    """
    Create one notification shared with all eligible users
    in the specified company.
    """

    notification = Notification(
        company_id=company_id,
        title=title,
        message=message,
        notification_type=notification_type,
        prediction_id=prediction_id
    )

    db.add(notification)
    db.flush()

    return notification
