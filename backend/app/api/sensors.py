from datetime import datetime, timezone

from app.core.security import verify_sensor_token
from app.models.network_event import NetworkEvent
from app.schemas.sensor import SensorNetworkEventCreate
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_role,
    is_super_admin
)

from app.core.security import (
    generate_sensor_token,
    hash_sensor_token
)

from app.models.user import User
from app.models.factory import Factory
from app.models.factory_sensor import FactorySensor

from app.schemas.sensor import (
    SensorCreate,
    SensorRegistrationResponse
)


router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"]
)


@router.post(
    "/",
    response_model=SensorRegistrationResponse,
    status_code=status.HTTP_201_CREATED
)
def register_sensor(
    sensor_data: SensorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    # Check that the target factory exists and is active
    factory_query = db.query(Factory).filter(
        Factory.id == sensor_data.factory_id,
        Factory.is_active.is_(True)
    )

    # Admin can only register sensors in their own company
    if not is_super_admin(current_user, db):
        factory_query = factory_query.filter(
            Factory.company_id == current_user.company_id
        )

    factory = factory_query.first()

    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    # Generate a one-time sensor token
    sensor_token = generate_sensor_token()

    new_sensor = FactorySensor(
        factory_id=factory.id,
        name=sensor_data.name,
        token_hash=hash_sensor_token(sensor_token),
        is_active=True
    )

    try:
        db.add(new_sensor)
        db.commit()
        db.refresh(new_sensor)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register sensor"
        )

    # Return the original token only once
    return SensorRegistrationResponse(
        id=new_sensor.id,
        name=new_sensor.name,
        factory_id=new_sensor.factory_id,
        is_active=new_sensor.is_active,
        created_at=new_sensor.created_at,
        sensor_token=sensor_token
    )


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED
)
def receive_sensor_event(
    event_data: SensorNetworkEventCreate,
    x_sensor_token: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    # Require a sensor token
    if not x_sensor_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sensor token is required"
        )

    # Find the sensor by verifying its token hash
    sensors = db.query(FactorySensor).filter(
        FactorySensor.is_active.is_(True)
    ).all()

    sensor = None

    for candidate in sensors:
        if verify_sensor_token(
            x_sensor_token,
            candidate.token_hash
        ):
            sensor = candidate
            break

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sensor token"
        )

    # Find the sensor's active factory
    factory = db.query(Factory).filter(
        Factory.id == sensor.factory_id,
        Factory.is_active.is_(True)
    ).first()

    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor factory is inactive or unavailable"
        )

    # Create event using trusted factory/company ownership
    new_event = NetworkEvent(
        **event_data.model_dump(),
        factory_id=factory.id,
        company_id=factory.company_id
    )

    try:
        db.add(new_event)

        sensor.last_seen = datetime.now(timezone.utc)

        db.commit()
        db.refresh(new_event)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save sensor event"
        )

    return {
        "message": "Sensor event received successfully",
        "event_id": new_event.id,
        "sensor_id": sensor.id,
        "factory_id": factory.id
    }
