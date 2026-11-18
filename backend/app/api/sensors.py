
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_role,
    is_super_admin
)

from app.core.security import (
    generate_sensor_token,
    hash_sensor_token,
    verify_sensor_token
)

from app.models.user import User
from app.models.factory import Factory
from app.models.factory_sensor import FactorySensor
from app.models.network_event import NetworkEvent

from app.schemas.sensor import (
    SensorCreate,
    SensorRegistrationResponse,
    SensorNetworkEventCreate,
    SensorListResponse,
    SensorStatusUpdate,
    SensorDashboardSummaryResponse,
    FactorySensorDashboardResponse
)
router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"]
)


# ==========================================
# Register a new factory sensor
# ==========================================

@router.post(
    "/",
    response_model=SensorRegistrationResponse,
    status_code=status.HTTP_201_CREATED
)
def register_sensor(
    sensor_data: SensorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    factory_query = db.query(Factory).filter(
        Factory.id == sensor_data.factory_id,
        Factory.is_active.is_(True)
    )

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

    return SensorRegistrationResponse(
        id=new_sensor.id,
        name=new_sensor.name,
        factory_id=new_sensor.factory_id,
        is_active=new_sensor.is_active,
        created_at=new_sensor.created_at,
        sensor_token=sensor_token
    )


# ==========================================
# Receive network events from factory sensors
# ==========================================

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

    # Find the sensor using its token hash
    token_hash = hash_sensor_token(x_sensor_token)

    sensor = db.query(FactorySensor).filter(
        FactorySensor.token_hash == token_hash,
        FactorySensor.is_active.is_(True)
    ).first()

    # Verify the token securely
    if sensor is None or not verify_sensor_token(
        x_sensor_token,
        sensor.token_hash
    ):
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

    # Assign factory and company from trusted database records
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

# ==========================================
# Sensor Heartbeat
# ==========================================

@router.post("/heartbeat")
def sensor_heartbeat(
    x_sensor_token: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    # Require a sensor token
    if not x_sensor_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sensor token is required"
        )

    # Find sensor using token hash
    token_hash = hash_sensor_token(x_sensor_token)

    sensor = db.query(FactorySensor).filter(
        FactorySensor.token_hash == token_hash,
        FactorySensor.is_active.is_(True)
    ).first()

    # Verify sensor token
    if sensor is None or not verify_sensor_token(
        x_sensor_token,
        sensor.token_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sensor token"
        )

    # Check that the sensor's factory is active
    factory = db.query(Factory).filter(
        Factory.id == sensor.factory_id,
        Factory.is_active.is_(True)
    ).first()

    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor factory is inactive or unavailable"
        )

    # Update last heartbeat time
    sensor.last_seen = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(sensor)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update sensor heartbeat"
        )

    return {
        "message": "Sensor heartbeat received successfully",
        "sensor_id": sensor.id,
        "factory_id": factory.id,
        "last_seen": sensor.last_seen
    }

# ==========================================
# Sensor Dashboard Summary
# ==========================================

@router.get(
    "/dashboard/summary",
    response_model=SensorDashboardSummaryResponse
)
def get_sensor_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    # Get sensors together with their factory status
    sensors_query = db.query(
        FactorySensor,
        Factory.is_active
    ).join(
        Factory,
        Factory.id == FactorySensor.factory_id
    )

    # Restrict regular admins to their own company
    if not is_super_admin(current_user, db):
        sensors_query = sensors_query.filter(
            Factory.company_id == current_user.company_id
        )

    sensor_records = sensors_query.all()

    now = datetime.now(timezone.utc)
    online_threshold = now - timedelta(minutes=5)

    # Initialize counters
    total_sensors = len(sensor_records)
    online_sensors = 0
    offline_sensors = 0
    inactive_sensors = 0

    # Calculate sensor statuses
    for sensor, factory_is_active in sensor_records:

        if not sensor.is_active or not factory_is_active:
            inactive_sensors += 1

        elif sensor.last_seen is None:
            offline_sensors += 1

        else:
            last_seen = sensor.last_seen

            # Handle databases returning naive datetimes
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(
                    tzinfo=timezone.utc
                )

            if last_seen >= online_threshold:
                online_sensors += 1
            else:
                offline_sensors += 1

    return SensorDashboardSummaryResponse(
        total_sensors=total_sensors,
        online_sensors=online_sensors,
        offline_sensors=offline_sensors,
        inactive_sensors=inactive_sensors
    )
# ==========================================
# Factory Sensors Dashboard
# ==========================================

@router.get(
    "/dashboard/factories",
    response_model=list[FactorySensorDashboardResponse]
)
def get_factory_sensor_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
  # Get factories based on user permissions
    factories_query = db.query(Factory)

    if not is_super_admin(current_user, db):
        factories_query = factories_query.filter(
            Factory.company_id == current_user.company_id
        )

    factories = factories_query.order_by(Factory.id).all()

    # Get sensors belonging to the allowed factories
    sensors_query = db.query(FactorySensor).join(
        Factory,
        Factory.id == FactorySensor.factory_id
    )

    if not is_super_admin(current_user, db):
        sensors_query = sensors_query.filter(
            Factory.company_id == current_user.company_id
        )

    sensors = sensors_query.all()

    # Group sensors by factory
    sensors_by_factory = {}

    for sensor in sensors:
        sensors_by_factory.setdefault(sensor.factory_id, []).append(sensor)

    now = datetime.now(timezone.utc)
    online_threshold = now - timedelta(minutes=5)

    factory_results = []

    for factory in factories:
        total_sensors = 0
        online_sensors = 0
        offline_sensors = 0
        inactive_sensors = 0

        factory_sensors = sensors_by_factory.get(factory.id, [])

        for sensor in factory_sensors:
            total_sensors += 1

            if not sensor.is_active or not factory.is_active:
                inactive_sensors += 1

            elif sensor.last_seen is None:
                offline_sensors += 1

            else:
                last_seen = sensor.last_seen

                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)

                if last_seen >= online_threshold:
                    online_sensors += 1
                else:
                    offline_sensors += 1

        factory_results.append(
            FactorySensorDashboardResponse(
                factory_id=factory.id,
                factory_name=factory.name,
                factory_location=factory.location,
                company_id=factory.company_id,
                factory_is_active=factory.is_active,
                total_sensors=total_sensors,
                online_sensors=online_sensors,
                offline_sensors=offline_sensors,
                inactive_sensors=inactive_sensors
            )
        )

    return factory_results

# ==========================================
# List factory sensors
# ==========================================

@router.get(
    "/",
    response_model=list[SensorListResponse]
)
def list_sensors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    # Get sensors together with their factory status
    sensors_query = db.query(
        FactorySensor,
        Factory.is_active
    ).join(
        Factory,
        Factory.id == FactorySensor.factory_id
    )

    # Restrict regular admins to their own company
    if not is_super_admin(current_user, db):
        sensors_query = sensors_query.filter(
            Factory.company_id == current_user.company_id
        )

    sensors_query = sensors_query.order_by(
        FactorySensor.created_at.desc()
    )

    sensor_records = sensors_query.all()

    now = datetime.now(timezone.utc)
    online_threshold = now - timedelta(minutes=5)

    results = []

    for sensor, factory_is_active in sensor_records:

        # Disabled sensor or inactive factory
        if not sensor.is_active or not factory_is_active:
            sensor_status = "Inactive"

        # Sensor has never sent a heartbeat or event
        elif sensor.last_seen is None:
            sensor_status = "Offline"

        else:
            last_seen = sensor.last_seen

            # Handle databases that return naive datetimes
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)

            if last_seen >= online_threshold:
                sensor_status = "Online"
            else:
                sensor_status = "Offline"

        results.append(
            SensorListResponse(
                id=sensor.id,
                name=sensor.name,
                factory_id=sensor.factory_id,
                is_active=sensor.is_active,
                last_seen=sensor.last_seen,
                created_at=sensor.created_at,
                status=sensor_status
            )
        )

    return results

# ==========================================
# Get sensor details
# ==========================================

@router.get(
    "/{sensor_id}",
    response_model=SensorListResponse
)
def get_sensor_details(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    # Find sensor together with its factory status
    sensor_record = db.query(
        FactorySensor,
        Factory.is_active
    ).join(
        Factory,
        Factory.id == FactorySensor.factory_id
    ).filter(
        FactorySensor.id == sensor_id
    )

    # Restrict regular admins to their own company
    if not is_super_admin(current_user, db):
        sensor_record = sensor_record.filter(
            Factory.company_id == current_user.company_id
        )

    result = sensor_record.first()

    # Do not reveal sensors belonging to other companies
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )

    sensor, factory_is_active = result

    # Determine current sensor status
    now = datetime.now(timezone.utc)
    online_threshold = now - timedelta(minutes=5)

    if not sensor.is_active or not factory_is_active:
        sensor_status = "Inactive"

    elif sensor.last_seen is None:
        sensor_status = "Offline"

    else:
        last_seen = sensor.last_seen

        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        if last_seen >= online_threshold:
            sensor_status = "Online"
        else:
            sensor_status = "Offline"

    return SensorListResponse(
        id=sensor.id,
        name=sensor.name,
        factory_id=sensor.factory_id,
        is_active=sensor.is_active,
        last_seen=sensor.last_seen,
        created_at=sensor.created_at,
        status=sensor_status
    )
# ==========================================
# Activate / Deactivate Sensor
# ==========================================

@router.patch(
    "/{sensor_id}/status",
    response_model=SensorListResponse
)
def update_sensor_status(
    sensor_id: int,
    status_data: SensorStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    sensor_record = db.query(
        FactorySensor,
        Factory.is_active
    ).join(
        Factory,
        Factory.id == FactorySensor.factory_id
    ).filter(
        FactorySensor.id == sensor_id
    )

    # Regular Admin can manage sensors in their company only.
    # Super Admin can manage sensors across all companies.
    if not is_super_admin(current_user, db):
        sensor_record = sensor_record.filter(
            Factory.company_id == current_user.company_id
        )

    result = sensor_record.first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )

    sensor, factory_is_active = result

    # Update sensor activation state.
    sensor.is_active = status_data.is_active

    try:
        db.commit()
        db.refresh(sensor)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update sensor status"
        )

    # Determine the updated sensor status.
    now = datetime.now(timezone.utc)
    online_threshold = now - timedelta(minutes=5)

    if not sensor.is_active or not factory_is_active:
        sensor_status = "Inactive"

    elif sensor.last_seen is None:
        sensor_status = "Offline"

    else:
        last_seen = sensor.last_seen

        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        if last_seen >= online_threshold:
            sensor_status = "Online"
        else:
            sensor_status = "Offline"

    return SensorListResponse(
        id=sensor.id,
        name=sensor.name,
        factory_id=sensor.factory_id,
        is_active=sensor.is_active,
        last_seen=sensor.last_seen,
        created_at=sensor.created_at,
        status=sensor_status
    )