from datetime import datetime

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
import app.database.init_db

from app.core.dependencies import get_db, get_current_user
from app.models.company import Company
from app.models.role import Role
from app.models.user import User
from app.models.notification import Notification, NotificationRead
from app.api.notifications import router as notifications_router


@pytest.fixture
def notification_api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    db = TestingSessionLocal()

    # Create two companies and one role.
    company_a = Company(
        name="Notification Test Company A",
        industry="Technology"
    )

    company_b = Company(
        name="Notification Test Company B",
        industry="Manufacturing"
    )

    role = Role(
        name="Notification Test Analyst",
        description="Test role"
    )

    db.add_all([company_a, company_b, role])
    db.commit()

    # All users were created before the test notification.
    account_date = datetime(2025, 1, 1)
    notification_date = datetime(2026, 1, 1)

    user1 = User(
        username="notification_user_1",
        email="notification1@test.com",
        hashed_password="test_hash",
        company_id=company_a.id,
        role_id=role.id,
        is_active=True,
        created_at=account_date
    )

    user2 = User(
        username="notification_user_2",
        email="notification2@test.com",
        hashed_password="test_hash",
        company_id=company_a.id,
        role_id=role.id,
        is_active=True,
        created_at=account_date
    )

    user3 = User(
        username="notification_user_3",
        email="notification3@test.com",
        hashed_password="test_hash",
        company_id=company_b.id,
        role_id=role.id,
        is_active=True,
        created_at=account_date
    )

    db.add_all([user1, user2, user3])
    db.commit()

    notification = Notification(
        company_id=company_a.id,
        title="Shared Security Alert",
        message="Suspicious activity detected.",
        notification_type="warning",
        created_at=notification_date
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Build a small FastAPI application for isolated API tests.
    app = FastAPI()
    app.include_router(notifications_router)

    state = {"current_user": user1}

    def override_get_db():
        yield db

    def override_get_current_user():
        return state["current_user"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    client = TestClient(app)

    yield {
        "client": client,
        "db": db,
        "state": state,
        "user1": user1,
        "user2": user2,
        "user3": user3,
        "notification": notification
    }

    client.close()
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_notification_read_is_independent_per_user(notification_api):
    client = notification_api["client"]
    state = notification_api["state"]
    user1 = notification_api["user1"]
    user2 = notification_api["user2"]
    notification = notification_api["notification"]
    db = notification_api["db"]

    # User 1 initially sees the notification as unread.
    state["current_user"] = user1

    response = client.get("/notifications/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["is_read"] is False

    # User 1 marks it as read.
    response = client.patch(
        f"/notifications/{notification.id}/read"
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is True

    # User 2 must still see it as unread.
    state["current_user"] = user2

    response = client.get("/notifications/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["is_read"] is False

    # User 2 must have one unread notification.
    response = client.get("/notifications/unread-count")

    assert response.status_code == 200
    assert response.json()["unread_count"] == 1

    # User 1 must have zero unread notifications.
    state["current_user"] = user1

    response = client.get("/notifications/unread-count")

    assert response.status_code == 200
    assert response.json()["unread_count"] == 0

    # Verify each user has a separate read record.
    records = (
        db.query(NotificationRead)
        .filter(
            NotificationRead.notification_id == notification.id
        )
        .all()
    )

    assert len(records) == 1
    assert records[0].user_id == user1.id
    assert records[0].is_read is True


def test_mark_notification_read_twice_does_not_duplicate(notification_api):
    client = notification_api["client"]
    notification = notification_api["notification"]
    user1 = notification_api["user1"]
    db = notification_api["db"]

    notification_id = notification.id

    for _ in range(2):
        response = client.patch(
            f"/notifications/{notification_id}/read"
        )

        assert response.status_code == 200
        assert response.json()["is_read"] is True

    records = (
        db.query(NotificationRead)
        .filter(
            NotificationRead.notification_id == notification_id,
            NotificationRead.user_id == user1.id
        )
        .all()
    )

    assert len(records) == 1


def test_company_isolation(notification_api):
    client = notification_api["client"]
    state = notification_api["state"]
    user3 = notification_api["user3"]
    notification = notification_api["notification"]

    # User 3 belongs to another company.
    state["current_user"] = user3

    response = client.get("/notifications/")

    assert response.status_code == 200
    assert response.json() == []

    response = client.get("/notifications/unread-count")

    assert response.status_code == 200
    assert response.json()["unread_count"] == 0

    response = client.patch(
        f"/notifications/{notification.id}/read"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"
def test_super_admin_can_see_notifications_from_all_companies(notification_api):
    client = notification_api["client"]
    state = notification_api["state"]
    db = notification_api["db"]
    user3 = notification_api["user3"]

    # Create Super Admin role.
    super_admin_role = Role(
        name="Super Admin",
        description="Platform-wide administrator"
    )

    db.add(super_admin_role)
    db.commit()
    db.refresh(super_admin_role)

    # Create Super Admin account.
    super_admin = User(
        username="notification_super_admin",
        email="superadmin_notification@test.com",
        hashed_password="test_hash",
        company_id=user3.company_id,
        role_id=super_admin_role.id,
        is_active=True,
        created_at=datetime(2025, 1, 1)
    )

    db.add(super_admin)
    db.commit()
    db.refresh(super_admin)

    # Create a notification for Company B.
    company_b_notification = Notification(
        company_id=user3.company_id,
        title="Company B Security Alert",
        message="Security event detected in Company B.",
        notification_type="warning",
        created_at=datetime(2026, 2, 1)
    )

    db.add(company_b_notification)
    db.commit()
    db.refresh(company_b_notification)

    # Super Admin should see notifications from both companies.
    state["current_user"] = super_admin

    response = client.get("/notifications/")

    assert response.status_code == 200

    notification_ids = {
        item["id"] for item in response.json()
    }

    assert notification_api["notification"].id in notification_ids
    assert company_b_notification.id in notification_ids


def test_user_cannot_see_notifications_created_before_account(notification_api):
    client = notification_api["client"]
    state = notification_api["state"]
    db = notification_api["db"]
    user1 = notification_api["user1"]

    # Create a user whose account starts in June 2026.
    new_user = User(
        username="notification_new_user",
        email="new_notification_user@test.com",
        hashed_password="test_hash",
        company_id=user1.company_id,
        role_id=user1.role_id,
        is_active=True,
        created_at=datetime(2026, 6, 1)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create an old notification.
    old_notification = Notification(
        company_id=user1.company_id,
        title="Old Security Alert",
        message="This notification is older than the account.",
        notification_type="info",
        created_at=datetime(2026, 5, 1)
    )

    # Create a notification after account creation.
    new_notification = Notification(
        company_id=user1.company_id,
        title="New Security Alert",
        message="This notification was created after the account.",
        notification_type="warning",
        created_at=datetime(2026, 7, 1)
    )

    db.add_all([old_notification, new_notification])
    db.commit()
    db.refresh(old_notification)
    db.refresh(new_notification)

    state["current_user"] = new_user

    response = client.get("/notifications/")

    assert response.status_code == 200

    notification_ids = {
        item["id"] for item in response.json()
    }

    assert new_notification.id in notification_ids
    assert old_notification.id not in notification_ids