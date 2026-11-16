from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, is_super_admin
from app.models.user import User
from app.models.notification import Notification, NotificationRead
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_visible_notifications_query(db, current_user):
    query = db.query(Notification)

    # Super Admin can see notifications from all companies.
    if not is_super_admin(current_user, db):
        query = query.filter(
            Notification.company_id == current_user.company_id
        )

    # Every user can only see notifications created
    # on or after their account creation date.
    query = query.filter(
        Notification.created_at >= current_user.created_at
    )

    return query
@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = get_visible_notifications_query(
        db, current_user
    ).order_by(Notification.created_at.desc()).all()

    response = []

    for notification in results:
        read_record = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification.id,
            NotificationRead.user_id == current_user.id,
            NotificationRead.is_read == True
        ).first()

        item = NotificationResponse(
            id=notification.id,
            company_id=notification.company_id,
            prediction_id=notification.prediction_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            is_read=read_record is not None,
            created_at=notification.created_at
        )

        response.append(item)

    return response


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifications = get_visible_notifications_query(
        db, current_user
    ).all()

    unread_count = 0

    for notification in notifications:
        read_record = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification.id,
            NotificationRead.user_id == current_user.id,
            NotificationRead.is_read == True
        ).first()

        if read_record is None:
            unread_count += 1

    return {"unread_count": unread_count}


@router.patch("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = get_visible_notifications_query(
        db, current_user
    ).filter(Notification.id == notification_id).first()

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    read_record = db.query(NotificationRead).filter(
        NotificationRead.notification_id == notification.id,
        NotificationRead.user_id == current_user.id
    ).first()

    if read_record is None:
        read_record = NotificationRead(
            notification_id=notification.id,
            user_id=current_user.id,
            is_read=True,
            read_at=datetime.now(timezone.utc)
        )
        db.add(read_record)
    else:
        read_record.is_read = True
        read_record.read_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Notification marked as read",
        "notification_id": notification.id,
        "is_read": True
    }