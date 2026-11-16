import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
import app.database.init_db
from app.models.company import Company
from app.models.notification import Notification
from app.services.notification_service import create_company_notification


@pytest.fixture
def db():
    engine = create_engine("sqlite://")

    # Create all project tables in the temporary SQLite database.
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_test_company(db):
    company = Company(
        name="Test Notification Company",
        industry="Technology"
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


def test_create_company_notification(db):
    company = create_test_company(db)

    notification = create_company_notification(
        db=db,
        company_id=company.id,
        title="Test Security Alert",
        message="A suspicious activity was detected."
    )

    assert notification.id is not None
    assert notification.company_id == company.id
    assert notification.title == "Test Security Alert"
    assert notification.notification_type == "info"

    notification_id = notification.id

    db.commit()
    db.expunge_all()

    saved_notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert saved_notification is not None
    assert saved_notification.message == (
        "A suspicious activity was detected."
    )


def test_create_critical_notification(db):
    company = create_test_company(db)

    notification = create_company_notification(
        db=db,
        company_id=company.id,
        title="Critical Security Threat",
        message="A malicious attack was detected.",
        notification_type="critical"
    )

    assert notification.notification_type == "critical"
    assert notification.company_id == company.id
    assert notification.id is not None


def test_notification_rollback(db):
    company = create_test_company(db)

    notification = create_company_notification(
        db=db,
        company_id=company.id,
        title="Temporary Alert",
        message="This notification will be rolled back."
    )

    notification_id = notification.id

    db.rollback()

    saved_notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert saved_notification is None
