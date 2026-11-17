from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models.company import Company
from app.models.factory import Factory
from app.models.factory_sensor import FactorySensor


def test_factory_sensor_creation():

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSession = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSession()

    company = Company(name="Sensor Test Company")
    db.add(company)
    db.flush()

    factory = Factory(
        name="Sensor Test Factory",
        location="Cairo",
        company_id=company.id
    )

    db.add(factory)
    db.flush()

    sensor = FactorySensor(
        factory_id=factory.id,
        name="Factory Network Sensor",
        token_hash="a" * 64,
        is_active=True
    )

    db.add(sensor)
    db.commit()

    saved_sensor = db.query(FactorySensor).first()

    assert saved_sensor is not None
    assert saved_sensor.name == "Factory Network Sensor"
    assert saved_sensor.factory_id == factory.id
    assert saved_sensor.is_active is True
    assert saved_sensor.token_hash == "a" * 64
    assert saved_sensor.last_seen is None

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()