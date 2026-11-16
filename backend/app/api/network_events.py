from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.dependencies import get_db, require_role, is_super_admin
from app.models.user import User
from app.models.factory import Factory
from app.models.network_event import NetworkEvent
from app.schemas.network_event import (
    NetworkEventCreate,
    NetworkEventResponse
)

router = APIRouter(
    prefix="/network-events",
    tags=["Network Events"]
)


def get_target_factory(
    factory_id: int,
    db: Session,
    current_user: User
):
    query = db.query(Factory).filter(
        Factory.id == factory_id,
        Factory.is_active.is_(True)
    )

    # Ordinary users can only access factories in their company.
    # Super Admin can access factories across all companies.
    if not is_super_admin(current_user, db):
        query = query.filter(
            Factory.company_id == current_user.company_id
        )

    factory = query.first()

    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    return factory


@router.post(
    "/",
    response_model=NetworkEventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_network_event(
    event_data: NetworkEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    # Verify that the factory exists, is active,
    # and belongs to the user's company unless the user is Super Admin.
    factory = get_target_factory(
        factory_id=event_data.factory_id,
        db=db,
        current_user=current_user
    )

    # Always take company_id from the factory itself.
    # This prevents incorrect company ownership for Super Admin events.
    new_event = NetworkEvent(
        **event_data.model_dump(),
        company_id=factory.company_id
    )

    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save network event"
        )

    return new_event


@router.get(
    "/",
    response_model=list[NetworkEventResponse]
)
def get_network_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    query = db.query(NetworkEvent)

    # Super Admin can see events from every company.
    # Other users are restricted to their own company.
    if not is_super_admin(current_user, db):
        query = query.filter(
            NetworkEvent.company_id == current_user.company_id
        )

    events = query.order_by(
        NetworkEvent.created_at.desc()
    ).all()

    return events
