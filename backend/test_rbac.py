
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base
from app.core.dependencies import get_db
from app.core.security import hash_password, create_access_token

from app.models.company import Company
from app.models.role import Role
from app.models.user import User
from app.models.factory import Factory
from app.models.network_event import NetworkEvent
from app.models.uploaded_dataset import UploadedDataset
from app.models.prediction import Prediction
from app.models.notification import Notification, NotificationRead


# Temporary in-memory database
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)


@pytest.fixture
def test_environment():
    Base.metadata.create_all(
        bind=TEST_ENGINE,

         tables=[
            NotificationRead.__table__,
            Notification.__table__,
            Prediction.__table__,
            UploadedDataset.__table__,
            NetworkEvent.__table__,
            User.__table__,
            Factory.__table__,
            Role.__table__,
            Company.__table__
        ]
    )

    db = TestingSessionLocal()

    # Create two companies
    company1 = Company(name="Test Company One")
    company2 = Company(name="Test Company Two")

    db.add_all([company1, company2])
    db.flush()

    # Create roles
    admin_role = Role(name="Admin")
    analyst_role = Role(name="Security Analyst")
    super_admin_role = Role(name="Super Admin")

    db.add_all([
        admin_role,
        analyst_role,
        super_admin_role
    ])
    db.flush()

    # Create users
    admin = User(
        username="test_admin",
        email="admin@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=company1.id,
        role_id=admin_role.id,
        is_active=True
    )

    analyst = User(
        username="test_analyst",
        email="analyst@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=company1.id,
        role_id=analyst_role.id,
        is_active=True
    )

    foreign_user = User(
        username="foreign_user",
        email="foreign@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=company2.id,
        role_id=analyst_role.id,
        is_active=True
    )

    super_admin = User(
        username="test_super_admin",
        email="superadmin@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=company2.id,
        role_id=super_admin_role.id,
        is_active=True
    )

    db.add_all([
        admin,
        analyst,
        foreign_user,
        super_admin
    ])
    db.flush()

    company1_factory = Factory(
        name="Company One Factory",
        location="Cairo",
        company_id=company1.id
    )

    company2_factory = Factory(
        name="Company Two Factory",
        location="Alexandria",
        company_id=company2.id
    )

    db.add_all([company1_factory, company2_factory])
    db.commit()

    data = {
        "admin_id": admin.id,
        "super_admin_id": super_admin.id,
        "super_admin_role_id": super_admin_role.id,
        "analyst_id": analyst.id,
        "foreign_user_id": foreign_user.id,
        "company1_id": company1.id,
        "company2_id": company2.id,
        "company1_factory_id": company1_factory.id,
        "company2_factory_id": company2_factory.id,
        "admin_role_id": admin_role.id,
        "analyst_role_id": analyst_role.id
    }

    db.close()

    # Override database dependency
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, data

    app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(
        bind=TEST_ENGINE,
          tables=[
            NotificationRead.__table__,
            Notification.__table__,
            Prediction.__table__,
            UploadedDataset.__table__,
            NetworkEvent.__table__,
            User.__table__,
            Factory.__table__,
            Role.__table__,
            Company.__table__
        ]
    )


def make_headers(user_id):
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


# Test 1: Reject requests without authentication
def test_users_reject_unauthenticated_request(test_environment):
    client, data = test_environment

    response = client.get("/users/")

    assert response.status_code == 401


# Test 2: Admin can list users in own company
def test_admin_can_list_company_users(test_environment):
    client, data = test_environment

    response = client.get(
        "/users/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


# Test 3: Analyst can list users in own company
def test_analyst_can_list_company_users(test_environment):
    client, data = test_environment

    response = client.get(
        "/users/",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


# Test 4: Analyst cannot update users
def test_analyst_cannot_update_users(test_environment):
    client, data = test_environment

    response = client.put(
        f"/users/{data['analyst_id']}",
        headers=make_headers(data["analyst_id"]),
        json={"username": "changed_name"}
    )

    assert response.status_code == 403


# Test 5: Analyst cannot deactivate users
def test_analyst_cannot_delete_users(test_environment):
    client, data = test_environment

    response = client.delete(
        f"/users/{data['analyst_id']}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 403


# Test 6: Analyst cannot register users
def test_analyst_cannot_register_users(test_environment):
    client, data = test_environment

    response = client.post(
        "/users/register",
        headers=make_headers(data["analyst_id"]),
        json={
            "username": "new_user",
            "email": "new@example.com",
            "password": "TestPassword123!",
            "company_id": data["company1_id"],
            "role_id": data["analyst_role_id"]
        }
    )

    assert response.status_code == 403


# Test 7: User cannot access another company's user
def test_cross_company_access_is_rejected(test_environment):
    client, data = test_environment

    response = client.get(
        f"/users/{data['foreign_user_id']}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 404


# Test 8: Admin registration uses admin's company
def test_admin_registration_uses_own_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/users/register",
        headers=make_headers(data["admin_id"]),
        json={
            "username": "new_company_user",
            "email": "new_company_user@example.com",
            "password": "TestPassword123!",
            "company_id": data["company2_id"],
            "role_id": data["analyst_role_id"]
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]


# Test 9: Admin role cannot be assigned through registration
def test_admin_role_assignment_is_rejected(test_environment):
    client, data = test_environment

    response = client.post(
        "/users/register",
        headers=make_headers(data["admin_id"]),
        json={
            "username": "another_admin",
            "email": "another_admin@example.com",
            "password": "TestPassword123!",
            "company_id": data["company1_id"],
            "role_id": data["admin_role_id"]
        }
    )

    assert response.status_code == 403


# Test 10: Admin cannot promote another user to Admin
def test_admin_cannot_assign_admin_role(test_environment):
    client, data = test_environment

    response = client.put(
        f"/users/{data['analyst_id']}",
        headers=make_headers(data["admin_id"]),
        json={"role_id": data["admin_role_id"]}
    )

    assert response.status_code == 403


# Test 11: Last active Admin cannot be deactivated
def test_last_admin_cannot_be_deactivated(test_environment):
    client, data = test_environment

    response = client.delete(
        f"/users/{data['admin_id']}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 400


# Test 12: Admin cannot deactivate their own account
def test_admin_cannot_deactivate_own_account(test_environment):
    client, data = test_environment

    # Add a second active Admin in the same company
    db = TestingSessionLocal()

    second_admin = User(
        username="second_admin",
        email="second_admin@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=data["company1_id"],
        role_id=data["admin_role_id"],
        is_active=True
    )

    db.add(second_admin)
    db.commit()
    db.close()

    # The first Admin tries to deactivate their own account
    response = client.delete(
        f"/users/{data['admin_id']}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 403


# Test 13: Admin can list only factories in own company
def test_admin_can_list_only_company_factories(test_environment):
    client, data = test_environment

    response = client.get(
        "/factories/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200

    factory_ids = [factory["id"] for factory in response.json()]

    assert data["company1_factory_id"] in factory_ids
    assert data["company2_factory_id"] not in factory_ids


# Test 14: Analyst can list only factories in own company
def test_analyst_can_list_only_company_factories(test_environment):
    client, data = test_environment

    response = client.get(
        "/factories/",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200

    factory_ids = [factory["id"] for factory in response.json()]

    assert data["company1_factory_id"] in factory_ids
    assert data["company2_factory_id"] not in factory_ids


# Test 15: Admin cannot access another company's factory
def test_admin_cannot_access_foreign_factory(test_environment):
    client, data = test_environment

    response = client.get(
        f"/factories/{data['company2_factory_id']}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 404


# Test 16: Analyst cannot access another company's factory
def test_analyst_cannot_access_foreign_factory(test_environment):
    client, data = test_environment

    response = client.get(
        f"/factories/{data['company2_factory_id']}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 404


# Test 17: Analyst cannot create a factory
def test_analyst_cannot_create_factory(test_environment):
    client, data = test_environment

    response = client.post(
        "/factories/",
        headers=make_headers(data["analyst_id"]),
        json={
            "name": "Unauthorized Factory",
            "location": "Cairo"
        }
    )

    assert response.status_code == 403


# Test 18: Analyst cannot update a factory
def test_analyst_cannot_update_factory(test_environment):
    client, data = test_environment

    response = client.put(
        f"/factories/{data['company1_factory_id']}",
        headers=make_headers(data["analyst_id"]),
        json={"name": "Unauthorized Update"}
    )

    assert response.status_code == 403


# Test 19: Analyst cannot delete a factory
def test_analyst_cannot_delete_factory(test_environment):
    client, data = test_environment

    response = client.delete(
        f"/factories/{data['company1_factory_id']}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 403


# Test 20: Admin cannot update another company's factory
def test_admin_cannot_update_foreign_factory(test_environment):
    client, data = test_environment

    response = client.put(
        f"/factories/{data['company2_factory_id']}",
        headers=make_headers(data["admin_id"]),
        json={"name": "Unauthorized Update"}
    )

    assert response.status_code == 404


# Test 21: Admin cannot delete another company's factory
def test_admin_cannot_delete_foreign_factory(test_environment):
    client, data = test_environment

    response = client.delete(
        f"/factories/{data['company2_factory_id']}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 404


# Test 22: Admin can create a factory in own company
def test_admin_can_create_factory_in_own_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/factories/",
        headers=make_headers(data["admin_id"]),
        json={
            "name": "New Authorized Factory",
            "location": "Cairo"
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]


# Test 23: Soft delete preserves historical factory data
def test_admin_soft_delete_factory_preserves_history(test_environment):
    client, data = test_environment

    # Create historical records in the temporary test database
    db = TestingSessionLocal()

    factory_id = data["company1_factory_id"]
    company_id = data["company1_id"]
    user_id = data["admin_id"]

    dataset = UploadedDataset(
        company_id=company_id,
        factory_id=factory_id,
        uploaded_by=user_id,
        dataset_type="system_logs",
        filename="historical_system_logs.json",
        records_count=1,
        columns=["event_type"],
        records=[{"event_type": "login"}]
    )

    db.add(dataset)
    db.flush()

    dataset_id = dataset.id

    network_event = NetworkEvent(
        company_id=company_id,
        factory_id=factory_id,
        source_ip="192.168.1.10",
        destination_ip="192.168.1.20",
        protocol="TCP",
        source_port=5000,
        destination_port=443
    )

    prediction = Prediction(
        company_id=company_id,
        factory_id=factory_id,
        uploaded_dataset_id=dataset_id,
        model_name="Test Model",
        model_version="1.0",
        prediction_label="Normal",
        confidence_score=0.99
    )

    db.add_all([network_event, prediction])
    db.commit()
    db.close()

    # Perform soft delete through the API
    response = client.delete(
        f"/factories/{factory_id}",
        headers=make_headers(user_id)
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Verify factory is inactive and historical data still exists
    db = TestingSessionLocal()

    factory = db.query(Factory).filter(
        Factory.id == factory_id
    ).first()

    assert factory is not None
    assert factory.is_active is False

    assert db.query(NetworkEvent).filter(
        NetworkEvent.factory_id == factory_id
    ).count() == 1

    assert db.query(UploadedDataset).filter(
        UploadedDataset.id == dataset_id
    ).count() == 1

    assert db.query(Prediction).filter(
        Prediction.factory_id == factory_id
    ).count() == 1

    db.close()

    # Inactive factory must not appear in the list
    list_response = client.get(
        "/factories/",
        headers=make_headers(user_id)
    )

    assert list_response.status_code == 200
    assert all(
        item["id"] != factory_id
        for item in list_response.json()
    )

    # Inactive factory cannot be accessed or updated
    get_response = client.get(
        f"/factories/{factory_id}",
        headers=make_headers(user_id)
    )
    assert get_response.status_code == 404

    update_response = client.put(
        f"/factories/{factory_id}",
        json={"name": "Changed Factory"},
        headers=make_headers(user_id)
    )
    assert update_response.status_code == 404

    # Repeating delete must return 404
    second_delete = client.delete(
        f"/factories/{factory_id}",
        headers=make_headers(user_id)
    )
    assert second_delete.status_code == 404

# ==========================================
# Super Admin Tests
# ==========================================

# Test 24: Super Admin can list users from all companies
def test_super_admin_can_list_all_companies_users(test_environment):
    client, data = test_environment

    response = client.get(
        "/users/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 4


# Test 25: Super Admin can access users in another company
def test_super_admin_can_get_user_from_another_company(test_environment):
    client, data = test_environment

    response = client.get(
        f"/users/{data['admin_id']}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["id"] == data["admin_id"]
    assert response.json()["company_id"] == data["company1_id"]


# Test 26: Super Admin can update users in another company
def test_super_admin_can_update_user_in_another_company(test_environment):
    client, data = test_environment

    response = client.put(
        f"/users/{data['admin_id']}",
        headers=make_headers(data["super_admin_id"]),
        json={"username": "updated_global_admin"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "updated_global_admin"


# Test 27: Super Admin can register users in another company
def test_super_admin_can_register_user_in_another_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/users/register",
        headers=make_headers(data["super_admin_id"]),
        json={
            "username": "global_test_user",
            "email": "globaluser@example.com",
            "password": "TestPassword123!",
            "company_id": data["company1_id"],
            "role_id": data["analyst_role_id"]
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]
    assert response.json()["username"] == "global_test_user"


# Test 28: Ordinary Admin cannot create a Super Admin
def test_admin_cannot_create_super_admin(test_environment):
    client, data = test_environment

    response = client.post(
        "/users/register",
        headers=make_headers(data["admin_id"]),
        json={
            "username": "unauthorized_super",
            "email": "unauthorized_super@example.com",
            "password": "TestPassword123!",
            "company_id": data["company2_id"],
            "role_id": data["super_admin_role_id"]
        }
    )

    assert response.status_code == 403


# Test 29: Ordinary Admin cannot update or deactivate a Super Admin
def test_admin_cannot_manage_super_admin_in_own_company(test_environment):
    client, data = test_environment

    # Create a Super Admin inside company one for this test
    db = TestingSessionLocal()

    local_super_admin = User(
        username="local_super_admin",
        email="local_super_admin@example.com",
        hashed_password=hash_password("TestPassword123!"),
        company_id=data["company1_id"],
        role_id=data["super_admin_role_id"],
        is_active=True
    )

    db.add(local_super_admin)
    db.commit()
    db.refresh(local_super_admin)

    target_id = local_super_admin.id
    db.close()

    # Admin must not update this account
    update_response = client.put(
        f"/users/{target_id}",
        headers=make_headers(data["admin_id"]),
        json={"username": "unauthorized_change"}
    )

    assert update_response.status_code == 403

    # Admin must not deactivate this account
    delete_response = client.delete(
        f"/users/{target_id}",
        headers=make_headers(data["admin_id"])
    )

    assert delete_response.status_code == 403


# Test 30: Last active Super Admin cannot be deactivated
def test_last_super_admin_cannot_be_deactivated(test_environment):
    client, data = test_environment

    response = client.delete(
        f"/users/{data['super_admin_id']}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 400


# Test 31: Last active Super Admin cannot be demoted
def test_last_super_admin_cannot_be_demoted(test_environment):
    client, data = test_environment

    response = client.put(
        f"/users/{data['super_admin_id']}",
        headers=make_headers(data["super_admin_id"]),
        json={"role_id": data["analyst_role_id"]}
    )

    assert response.status_code == 400

# ==========================================
# Super Admin Factory Tests
# ==========================================

# Test 32: Super Admin can list factories from all companies
def test_super_admin_can_list_all_company_factories(test_environment):
    client, data = test_environment

    response = client.get(
        "/factories/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200

    factory_ids = [factory["id"] for factory in response.json()]

    assert data["company1_factory_id"] in factory_ids
    assert data["company2_factory_id"] in factory_ids


# Test 33: Super Admin can access a factory from another company
def test_super_admin_can_access_foreign_factory(test_environment):
    client, data = test_environment

    response = client.get(
        f"/factories/{data['company1_factory_id']}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == data["company1_id"]


# Test 34: Super Admin can create a factory for another company
def test_super_admin_can_create_factory_for_another_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/factories/",
        headers=make_headers(data["super_admin_id"]),
        json={
            "name": "Super Admin New Factory",
            "location": "Giza",
            "company_id": data["company1_id"]
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]
    assert response.json()["name"] == "Super Admin New Factory"


# Test 35: Super Admin cannot create a factory for a nonexistent company
def test_super_admin_cannot_create_factory_for_nonexistent_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/factories/",
        headers=make_headers(data["super_admin_id"]),
        json={
            "name": "Invalid Company Factory",
            "location": "Cairo",
            "company_id": 999999
        }
    )

    assert response.status_code == 404


# Test 36: Admin cannot override company_id when creating a factory
def test_admin_cannot_create_factory_in_another_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/factories/",
        headers=make_headers(data["admin_id"]),
        json={
            "name": "Admin Attempted Foreign Factory",
            "location": "Alexandria",
            "company_id": data["company2_id"]
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]


# Test 37: Super Admin can update a factory in another company
def test_super_admin_can_update_foreign_factory(test_environment):
    client, data = test_environment

    response = client.put(
        f"/factories/{data['company1_factory_id']}",
        headers=make_headers(data["super_admin_id"]),
        json={
            "name": "Updated By Super Admin",
            "location": "New Cairo"
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated By Super Admin"
    assert response.json()["company_id"] == data["company1_id"]


# Test 38: Super Admin can soft delete a factory in another company
def test_super_admin_can_soft_delete_foreign_factory(test_environment):
    client, data = test_environment

    factory_id = data["company1_factory_id"]

    response = client.delete(
        f"/factories/{factory_id}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Verify the factory still exists in the database
    db = TestingSessionLocal()

    try:
        factory = db.query(Factory).filter(
            Factory.id == factory_id
        ).first()

        assert factory is not None
        assert factory.is_active is False
        assert factory.company_id == data["company1_id"]

    finally:
        db.close()



# ==========================================
# Data Upload RBAC Tests
# ==========================================

def create_test_dataset(db, company_id, factory_id, uploaded_by, filename):
    dataset = UploadedDataset(
        company_id=company_id,
        factory_id=factory_id,
        uploaded_by=uploaded_by,
        dataset_type="traffic_logs",
        filename=filename,
        records_count=1,
        columns=["timestamp", "source_ip", "destination_ip", "protocol", "packet_count"],
        records=[{
            "timestamp": "2026-11-05T10:00:00",
            "source_ip": "192.168.1.10",
            "destination_ip": "192.168.1.20",
            "protocol": "TCP",
            "packet_count": 100
        }]
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


# Test 39: Super Admin can list datasets from all companies
def test_super_admin_can_list_all_company_datasets(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        create_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            "company_one.csv"
        )

        create_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"],
            "company_two.csv"
        )
    finally:
        db.close()

    response = client.get(
        "/data-upload/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200

    datasets = response.json()
    assert len(datasets) == 2

    company_ids = [dataset["company_id"] for dataset in datasets]

    assert data["company1_id"] in company_ids
    assert data["company2_id"] in company_ids


# Test 40: Admin can list datasets from own company only
def test_admin_can_list_only_company_datasets(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        create_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            "company_one.csv"
        )

        create_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"],
            "company_two.csv"
        )
    finally:
        db.close()

    response = client.get(
        "/data-upload/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200

    datasets = response.json()

    assert len(datasets) == 1
    assert datasets[0]["company_id"] == data["company1_id"]
    assert datasets[0]["filename"] == "company_one.csv"


# Test 41: Analyst cannot access a dataset from another company
def test_analyst_cannot_access_foreign_dataset(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        dataset = create_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"],
            "foreign_dataset.csv"
        )

        dataset_id = dataset.id
    finally:
        db.close()

    response = client.get(
        f"/data-upload/{dataset_id}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 404


# Test 42: Super Admin can access a dataset from another company
def test_super_admin_can_access_foreign_dataset(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        dataset = create_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            "company_one.csv"
        )

        dataset_id = dataset.id
    finally:
        db.close()

    response = client.get(
        f"/data-upload/{dataset_id}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == data["company1_id"]



# Test 43: Super Admin can upload to a factory in another company
def test_super_admin_can_upload_to_foreign_factory(test_environment):
    client, data = test_environment

    csv_content = (
        b"timestamp,source_ip,destination_ip,protocol,packet_count\n"
        b"2026-11-05T10:00:00,192.168.1.10,192.168.1.20,TCP,100"
    )

    expected_records = [
    {
        "timestamp": "2026-11-05T10:00:00",
        "source_ip": "192.168.1.10",
        "destination_ip": "192.168.1.20",
        "protocol": "TCP",
        "packet_count": 100,
        "source_port": None,
        "destination_port": None,
        "bytes_transferred": None,
        "duration": None
    }
]

    response = client.post(
        "/data-upload/",
        headers=make_headers(data["super_admin_id"]),
        data={
            "factory_id": str(data["company1_factory_id"]),
            "dataset_type": "traffic_logs"
        },
        files={
            "file": ("super_admin_upload.csv", csv_content, "text/csv")
        }
    )

    assert response.status_code == 201

    dataset_id = response.json()["dataset_id"]

    assert response.json()["company_id"] == data["company1_id"]
    assert response.json()["factory_id"] == data["company1_factory_id"]

    # Verify dataset metadata and normalized records were saved
    db = TestingSessionLocal()

    try:
        saved_dataset = db.query(UploadedDataset).filter(
            UploadedDataset.id == dataset_id
        ).first()

        assert saved_dataset is not None
        assert saved_dataset.company_id == data["company1_id"]
        assert saved_dataset.factory_id == data["company1_factory_id"]
        assert saved_dataset.uploaded_by == data["super_admin_id"]
        assert saved_dataset.records == expected_records
        assert saved_dataset.records_count == 1
        assert isinstance(saved_dataset.records[0]["packet_count"], int)

    finally:
        db.close()

    # Verify the GET details endpoint returns the saved records
    details_response = client.get(
        f"/data-upload/{dataset_id}",
        headers=make_headers(data["super_admin_id"])
    )

    assert details_response.status_code == 200
    assert details_response.json()["records"] == expected_records
    assert details_response.json()["records_count"] == 1



# Test 44: Admin cannot upload to another company's factory
def test_admin_cannot_upload_to_foreign_factory(test_environment):
    client, data = test_environment

    csv_content = (
        b"timestamp,source_ip,destination_ip,protocol,packet_count\n"
        b"2026-11-05T10:00:00,192.168.1.10,192.168.1.20,TCP,100"
    )

    response = client.post(
        "/data-upload/",
        headers=make_headers(data["admin_id"]),
        data={
            "factory_id": str(data["company2_factory_id"]),
            "dataset_type": "traffic_logs"
        },
        files={
            "file": ("admin_upload.csv", csv_content, "text/csv")
        }
    )

    assert response.status_code == 404


# Test 45: Upload to an inactive factory must be rejected
def test_upload_to_inactive_factory_is_rejected(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        factory = db.query(Factory).filter(
            Factory.id == data["company1_factory_id"]
        ).first()

        factory.is_active = False
        db.commit()
    finally:
        db.close()

    csv_content = (
        b"timestamp,source_ip,destination_ip,protocol,packet_count\n"
        b"2026-11-05T10:00:00,192.168.1.10,192.168.1.20,TCP,100"
    )

    response = client.post(
        "/data-upload/",
        headers=make_headers(data["admin_id"]),
        data={
            "factory_id": str(data["company1_factory_id"]),
            "dataset_type": "traffic_logs"
        },
        files={
            "file": ("inactive_factory.csv", csv_content, "text/csv")
        }
    )

    assert response.status_code == 404


# ==========================================
# Network Events RBAC Tests
# ==========================================

def create_test_network_event(db, company_id, factory_id):
    event = NetworkEvent(
        company_id=company_id,
        factory_id=factory_id,
        source_ip="192.168.1.10",
        destination_ip="192.168.1.20",
        protocol="TCP",
        source_port=5000,
        destination_port=443,
        packet_count=100,
        bytes_transferred=5000,
        duration=2.5
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# Test 46: Super Admin sees events from all companies
def test_super_admin_can_list_all_company_network_events(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        create_test_network_event(db, data["company1_id"], data["company1_factory_id"])
        create_test_network_event(db, data["company2_id"], data["company2_factory_id"])
    finally:
        db.close()

    response = client.get(
        "/network-events/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2

    company_ids = [event["company_id"] for event in events]
    assert data["company1_id"] in company_ids
    assert data["company2_id"] in company_ids


# Test 47: Admin sees only own company's events
def test_admin_can_list_only_company_network_events(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        create_test_network_event(db, data["company1_id"], data["company1_factory_id"])
        create_test_network_event(db, data["company2_id"], data["company2_factory_id"])
    finally:
        db.close()

    response = client.get(
        "/network-events/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["company_id"] == data["company1_id"]


# Test 48: Analyst sees only own company's events
def test_analyst_can_list_company_network_events(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        create_test_network_event(db, data["company1_id"], data["company1_factory_id"])
        create_test_network_event(db, data["company2_id"], data["company2_factory_id"])
    finally:
        db.close()

    response = client.get(
        "/network-events/",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["company_id"] == data["company1_id"]


# Test 49: Super Admin creates event for another company's factory
def test_super_admin_can_create_event_for_foreign_factory(test_environment):
    client, data = test_environment

    response = client.post(
        "/network-events/",
        headers=make_headers(data["super_admin_id"]),
        json={
            "factory_id": data["company1_factory_id"],
            "source_ip": "10.0.0.1",
            "destination_ip": "10.0.0.2",
            "protocol": "tcp",
            "source_port": 5000,
            "destination_port": 443,
            "packet_count": 200,
            "bytes_transferred": 10000,
            "duration": 3.5
        }
    )

    assert response.status_code == 201
    result = response.json()
    assert result["company_id"] == data["company1_id"]
    assert result["factory_id"] == data["company1_factory_id"]
    assert result["protocol"] == "TCP"


# Test 50: Admin cannot create event for another company's factory
def test_admin_cannot_create_event_for_foreign_factory(test_environment):
    client, data = test_environment

    response = client.post(
        "/network-events/",
        headers=make_headers(data["admin_id"]),
        json={
            "factory_id": data["company2_factory_id"],
            "source_ip": "10.0.0.1",
            "destination_ip": "10.0.0.2",
            "protocol": "TCP"
        }
    )

    assert response.status_code == 404


# Test 51: Analyst can create event in own company
def test_analyst_can_create_event_for_own_factory(test_environment):
    client, data = test_environment

    response = client.post(
        "/network-events/",
        headers=make_headers(data["analyst_id"]),
        json={
            "factory_id": data["company1_factory_id"],
            "source_ip": "10.0.0.1",
            "destination_ip": "10.0.0.2",
            "protocol": "UDP"
        }
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == data["company1_id"]


# Test 52: Inactive factory cannot receive network events
def test_network_event_rejected_for_inactive_factory(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        factory = db.query(Factory).filter(
            Factory.id == data["company1_factory_id"]
        ).first()

        factory.is_active = False
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/network-events/",
        headers=make_headers(data["admin_id"]),
        json={
            "factory_id": data["company1_factory_id"],
            "source_ip": "10.0.0.1",
            "destination_ip": "10.0.0.2",
            "protocol": "TCP"
        }
    )

    assert response.status_code == 404


# Test 53: Unauthenticated users cannot list network events
def test_network_events_reject_unauthenticated_request(test_environment):
    client, data = test_environment

    response = client.get("/network-events/")

    assert response.status_code == 401

# ============================================================
# Prediction RBAC Test Helpers
# ============================================================

def create_rbac_test_dataset(
    db,
    company_id,
    factory_id,
    uploaded_by,
    filename="test_dataset.csv",
    records_count=2
):
    dataset = UploadedDataset(
        company_id=company_id,
        factory_id=factory_id,
        uploaded_by=uploaded_by,
        dataset_type="system_logs",
        filename=filename,
        records_count=records_count,
        columns=["timestamp", "event"],
        records=[
            {"timestamp": "2026-11-05", "event": "login"},
            {"timestamp": "2026-11-05", "event": "logout"}
        ][:records_count]
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def create_rbac_test_prediction(db, dataset, label="normal", output=None):
    prediction = Prediction(
        company_id=dataset.company_id,
        factory_id=dataset.factory_id,
        uploaded_dataset_id=dataset.id,
        record_index=0,
        model_name="Test Model",
        model_version="1.0",
        prediction_label=label,
        confidence_score=0.95,
        prediction_output=output or {"status": label}
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction


# ============================================================
# Prediction RBAC Tests
# ============================================================

# Test 54: Super Admin can list predictions from all companies
def test_super_admin_can_list_all_company_predictions(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset1 = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        dataset2 = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        create_rbac_test_prediction(db, dataset1)
        create_rbac_test_prediction(db, dataset2)

    finally:
        db.close()

    response = client.get(
        "/predictions/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


# Test 55: Admin can list predictions from own company only
def test_admin_can_list_own_company_predictions_only(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset1 = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        dataset2 = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        create_rbac_test_prediction(db, dataset1)
        create_rbac_test_prediction(db, dataset2)

    finally:
        db.close()

    response = client.get(
        "/predictions/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company_id"] == data["company1_id"]


# Test 56: Analyst can list predictions from own company only
def test_analyst_can_list_own_company_predictions_only(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset1 = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        dataset2 = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        create_rbac_test_prediction(db, dataset1)
        create_rbac_test_prediction(db, dataset2)

    finally:
        db.close()

    response = client.get(
        "/predictions/",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company_id"] == data["company1_id"]


# Test 57: Super Admin can retrieve a foreign company prediction
def test_super_admin_can_get_foreign_company_prediction(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        prediction = create_rbac_test_prediction(db, dataset)
        prediction_id = prediction.id

    finally:
        db.close()

    response = client.get(
        f"/predictions/{prediction_id}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == data["company1_id"]


# Test 58: Admin cannot retrieve a foreign company prediction
def test_admin_cannot_get_foreign_company_prediction(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        prediction = create_rbac_test_prediction(db, dataset)
        prediction_id = prediction.id

    finally:
        db.close()

    response = client.get(
        f"/predictions/{prediction_id}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 404


# Test 59: Analyst cannot retrieve a foreign company prediction
def test_analyst_cannot_get_foreign_company_prediction(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        prediction = create_rbac_test_prediction(db, dataset)
        prediction_id = prediction.id

    finally:
        db.close()

    response = client.get(
        f"/predictions/{prediction_id}",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 404


# Test 60: Super Admin can create prediction from foreign dataset
# The notification must belong to the dataset's company.
def test_super_admin_can_create_foreign_prediction_and_notification(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        dataset_id = dataset.id

    finally:
        db.close()

    response = client.post(
        "/predictions/",
        headers=make_headers(data["super_admin_id"]),
        json={
            "uploaded_dataset_id": dataset_id,
            "record_index": 0,
            "model_name": "Test Security Model",
            "model_version": "1.0",
            "prediction_label": "malicious",
            "confidence_score": 0.99,
            "prediction_output": {"status": "malicious"}
        }
    )

    assert response.status_code == 201

    result = response.json()

    assert result["company_id"] == data["company1_id"]
    assert result["factory_id"] == data["company1_factory_id"]

    db = TestingSessionLocal()

    try:
        notification = db.query(Notification).filter(
            Notification.prediction_id == result["id"]
        ).first()

        assert notification is not None
        assert notification.company_id == data["company1_id"]
        assert notification.company_id != data["company2_id"]
        assert notification.notification_type == "critical"

    finally:
        db.close()


# Test 61: Admin cannot create prediction from foreign dataset
def test_admin_cannot_create_prediction_from_foreign_dataset(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        dataset_id = dataset.id

    finally:
        db.close()

    response = client.post(
        "/predictions/",
        headers=make_headers(data["admin_id"]),
        json={
            "uploaded_dataset_id": dataset_id,
            "model_name": "Test Model",
            "prediction_label": "normal"
        }
    )

    assert response.status_code == 404


# Test 62: Analyst cannot create prediction from foreign dataset
def test_analyst_cannot_create_prediction_from_foreign_dataset(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"]
        )

        dataset_id = dataset.id

    finally:
        db.close()

    response = client.post(
        "/predictions/",
        headers=make_headers(data["analyst_id"]),
        json={
            "uploaded_dataset_id": dataset_id,
            "model_name": "Test Model",
            "prediction_label": "normal"
        }
    )

    assert response.status_code == 404


# Test 63: Reject prediction record index outside dataset range
def test_prediction_rejects_record_index_outside_dataset(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            records_count=2
        )

        dataset_id = dataset.id

    finally:
        db.close()

    response = client.post(
        "/predictions/",
        headers=make_headers(data["admin_id"]),
        json={
            "uploaded_dataset_id": dataset_id,
            "record_index": 5,
            "model_name": "Test Model",
            "prediction_label": "normal"
        }
    )

    assert response.status_code == 400


# Test 64: Normal prediction does not create a notification
def test_normal_prediction_does_not_create_notification(test_environment):
    client, data = test_environment
    db = TestingSessionLocal()

    try:
        dataset = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"]
        )

        dataset_id = dataset.id

    finally:
        db.close()

    response = client.post(
        "/predictions/",
        headers=make_headers(data["analyst_id"]),
        json={
            "uploaded_dataset_id": dataset_id,
            "record_index": 0,
            "model_name": "Test Security Model",
            "prediction_label": "normal",
            "prediction_output": {"status": "normal"}
        }
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    try:
        notification_count = db.query(Notification).count()
        assert notification_count == 0

    finally:
        db.close()


# Test 65: Unauthenticated users cannot access predictions
def test_predictions_reject_unauthenticated_request(test_environment):
    client, data = test_environment

    response = client.get("/predictions/")

    assert response.status_code == 401


# ============================================================
# Dashboard RBAC Tests
# ============================================================

def seed_dashboard_test_data(data):
    db = TestingSessionLocal()

    try:
        dataset1 = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            filename="company_one.csv"
        )

        dataset2 = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"],
            filename="company_two.csv"
        )

        create_rbac_test_prediction(
            db,
            dataset1,
            label="normal"
        )

        create_rbac_test_prediction(
            db,
            dataset2,
            label="malicious"
        )

    finally:
        db.close()


# Test 66: Super Admin sees platform-wide dashboard statistics
def test_super_admin_can_view_platform_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 2
    assert result["total_records"] == 4
    assert result["total_predictions"] == 2
    assert len(result["factories"]) == 2

    assert sum(
        item["count"] for item in result["predictions_by_label"]
    ) == 2


# Test 67: Admin sees dashboard statistics for own company only
def test_admin_can_view_own_company_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 1
    assert result["total_records"] == 2
    assert result["total_predictions"] == 1
    assert len(result["factories"]) == 1

    assert result["factories"][0]["factory_id"] == data["company1_factory_id"]

    assert all(
        item["prediction_label"] == "normal"
        for item in result["predictions_by_label"]
    )


# Test 68: Analyst sees dashboard statistics for own company only
def test_analyst_can_view_own_company_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 1
    assert result["total_records"] == 2
    assert result["total_predictions"] == 1
    assert len(result["factories"]) == 1

    assert result["factories"][0]["factory_id"] == data["company1_factory_id"]


# Test 69: Unauthenticated users cannot access dashboard statistics
def test_dashboard_rejects_unauthenticated_request(test_environment):
    client, data = test_environment

    response = client.get("/dashboard/statistics")

    assert response.status_code == 401


# ============================================================
# Dashboard RBAC Tests
# ============================================================

def seed_dashboard_test_data(data):
    db = TestingSessionLocal()

    try:
        dataset1 = create_rbac_test_dataset(
            db,
            data["company1_id"],
            data["company1_factory_id"],
            data["admin_id"],
            filename="company_one.csv"
        )

        dataset2 = create_rbac_test_dataset(
            db,
            data["company2_id"],
            data["company2_factory_id"],
            data["foreign_user_id"],
            filename="company_two.csv"
        )

        create_rbac_test_prediction(
            db,
            dataset1,
            label="normal"
        )

        create_rbac_test_prediction(
            db,
            dataset2,
            label="malicious"
        )

    finally:
        db.close()


# Test 66: Super Admin sees platform-wide dashboard statistics
def test_super_admin_can_view_platform_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 2
    assert result["total_records"] == 4
    assert result["total_predictions"] == 2
    assert len(result["factories"]) == 2

    assert sum(
        item["count"] for item in result["predictions_by_label"]
    ) == 2


# Test 67: Admin sees dashboard statistics for own company only
def test_admin_can_view_own_company_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 1
    assert result["total_records"] == 2
    assert result["total_predictions"] == 1
    assert len(result["factories"]) == 1

    assert result["factories"][0]["factory_id"] == data["company1_factory_id"]

    assert all(
        item["prediction_label"] == "normal"
        for item in result["predictions_by_label"]
    )


# Test 68: Analyst sees dashboard statistics for own company only
def test_analyst_can_view_own_company_dashboard(test_environment):
    client, data = test_environment

    seed_dashboard_test_data(data)

    response = client.get(
        "/dashboard/statistics",
        headers=make_headers(data["analyst_id"])
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_datasets"] == 1
    assert result["total_records"] == 2
    assert result["total_predictions"] == 1
    assert len(result["factories"]) == 1

    assert result["factories"][0]["factory_id"] == data["company1_factory_id"]


# Test 69: Unauthenticated users cannot access dashboard statistics
def test_dashboard_rejects_unauthenticated_request(test_environment):
    client, data = test_environment

    response = client.get("/dashboard/statistics")

    assert response.status_code == 401


# ============================================================
# Companies RBAC Tests
# ============================================================

# Test 70: Super Admin can list all companies
def test_super_admin_can_list_all_companies(test_environment):
    client, data = test_environment

    response = client.get(
        "/companies/",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200

    companies = response.json()

    assert len(companies) == 2
    assert {company["id"] for company in companies} == {
        data["company1_id"],
        data["company2_id"]
    }


# Test 71: Super Admin can create a company
def test_super_admin_can_create_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/companies/",
        headers=make_headers(data["super_admin_id"]),
        json={
            "name": "New Test Company",
            "industry": "Manufacturing",
            "email": "newcompany@test.com"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "New Test Company"


# Test 72: Super Admin can view another company's details
def test_super_admin_can_view_foreign_company(test_environment):
    client, data = test_environment

    response = client.get(
        f"/companies/{data['company1_id']}",
        headers=make_headers(data["super_admin_id"])
    )

    assert response.status_code == 200
    assert response.json()["id"] == data["company1_id"]


# Test 73: Super Admin can update another company
def test_super_admin_can_update_foreign_company(test_environment):
    client, data = test_environment

    response = client.put(
        f"/companies/{data['company1_id']}",
        headers=make_headers(data["super_admin_id"]),
        json={
            "industry": "Updated Manufacturing"
        }
    )

    assert response.status_code == 200
    assert response.json()["industry"] == "Updated Manufacturing"


# Test 74: Admin cannot list all companies
def test_admin_cannot_list_all_companies(test_environment):
    client, data = test_environment

    response = client.get(
        "/companies/",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 403


# Test 75: Analyst cannot create a company
def test_analyst_cannot_create_company(test_environment):
    client, data = test_environment

    response = client.post(
        "/companies/",
        headers=make_headers(data["analyst_id"]),
        json={
            "name": "Unauthorized Company",
            "industry": "Testing"
        }
    )

    assert response.status_code == 403


# Test 76: Admin cannot view another company's details
def test_admin_cannot_view_foreign_company(test_environment):
    client, data = test_environment

    response = client.get(
        f"/companies/{data['company2_id']}",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 403


# Test 77: Unauthenticated users cannot list companies
def test_unauthenticated_user_cannot_list_companies(test_environment):
    client, data = test_environment

    response = client.get("/companies/")

    assert response.status_code == 401


# ============================================================
# Notifications RBAC Tests
# ============================================================

def test_super_admin_can_view_notifications_from_all_companies(test_environment):
    from datetime import datetime, timezone

    client, data = test_environment
    db = TestingSessionLocal()

    try:
        notifications = [
            Notification(
                company_id=data["company1_id"],
                title="Company One Alert",
                message="Alert from company one",
                notification_type="critical",
                created_at=datetime.now(timezone.utc)
            ),
            Notification(
                company_id=data["company2_id"],
                title="Company Two Alert",
                message="Alert from company two",
                notification_type="warning",
                created_at=datetime.now(timezone.utc)
            )
        ]

        db.add_all(notifications)
        db.commit()

        response = client.get(
            "/notifications/",
            headers=make_headers(data["super_admin_id"])
        )

        assert response.status_code == 200

        results = response.json()
        company_ids = {item["company_id"] for item in results}

        assert data["company1_id"] in company_ids
        assert data["company2_id"] in company_ids
        assert len(results) == 2

        unread_response = client.get(
            "/notifications/unread-count",
            headers=make_headers(data["super_admin_id"])
        )

        assert unread_response.status_code == 200
        assert unread_response.json()["unread_count"] == 2

    finally:
        db.close()


def test_admin_and_analyst_can_only_view_own_company_notifications(test_environment):
    from datetime import datetime, timezone

    client, data = test_environment
    db = TestingSessionLocal()

    try:
        db.add_all([
            Notification(
                company_id=data["company1_id"],
                title="Company One Alert",
                message="Own company notification",
                notification_type="warning",
                created_at=datetime.now(timezone.utc)
            ),
            Notification(
                company_id=data["company2_id"],
                title="Company Two Alert",
                message="Foreign company notification",
                notification_type="critical",
                created_at=datetime.now(timezone.utc)
            )
        ])
        db.commit()

        for user_id in [data["admin_id"], data["analyst_id"]]:
            response = client.get(
                "/notifications/",
                headers=make_headers(user_id)
            )

            assert response.status_code == 200

            results = response.json()

            assert len(results) == 1
            assert results[0]["company_id"] == data["company1_id"]
            assert results[0]["title"] == "Company One Alert"

    finally:
        db.close()


def test_notifications_respect_user_account_creation_date(test_environment):
    from datetime import timedelta, timezone

    client, data = test_environment
    db = TestingSessionLocal()

    try:
        user = db.query(User).filter(
            User.id == data["admin_id"]
        ).first()

        assert user is not None
        assert user.created_at is not None

        old_notification = Notification(
            company_id=data["company1_id"],
            title="Old Notification",
            message="Created before user account",
            notification_type="info",
            created_at=user.created_at - timedelta(days=1)
        )

        new_notification = Notification(
            company_id=data["company1_id"],
            title="New Notification",
            message="Created after user account",
            notification_type="info",
            created_at=user.created_at + timedelta(days=1)
        )

        db.add_all([old_notification, new_notification])
        db.commit()

        response = client.get(
            "/notifications/",
            headers=make_headers(data["admin_id"])
        )

        assert response.status_code == 200

        titles = {item["title"] for item in response.json()}

        assert "New Notification" in titles
        assert "Old Notification" not in titles

    finally:
        db.close()


def test_notification_read_status_is_independent_per_user(test_environment):
    from datetime import datetime, timezone

    client, data = test_environment
    db = TestingSessionLocal()

    try:
        notification = Notification(
            company_id=data["company1_id"],
            title="Independent Read Test",
            message="Read status must be per user",
            notification_type="warning",
            created_at=datetime.now(timezone.utc)
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        notification_id = notification.id

        # Super Admin reads the notification.
        super_response = client.patch(
            f"/notifications/{notification_id}/read",
            headers=make_headers(data["super_admin_id"])
        )

        assert super_response.status_code == 200
        assert super_response.json()["is_read"] is True

        # Admin must still see it as unread.
        admin_response = client.get(
            "/notifications/",
            headers=make_headers(data["admin_id"])
        )

        assert admin_response.status_code == 200

        admin_notification = next(
            item for item in admin_response.json()
            if item["id"] == notification_id
        )

        assert admin_notification["is_read"] is False

        # Admin reads the same notification independently.
        admin_read_response = client.patch(
            f"/notifications/{notification_id}/read",
            headers=make_headers(data["admin_id"])
        )

        assert admin_read_response.status_code == 200

        # Verify two separate read records exist.
        read_records = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id,
            NotificationRead.is_read == True
        ).all()

        assert len(read_records) == 2

        user_ids = {record.user_id for record in read_records}

        assert data["super_admin_id"] in user_ids
        assert data["admin_id"] in user_ids

    finally:
        db.close()


# ==========================================
# AUTHENTICATION TESTS
# ==========================================

def test_login_with_email(test_environment):
    client, data = test_environment

    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_with_username(test_environment):
    client, data = test_environment

    response = client.post(
        "/auth/login",
        data={
            "username": "test_admin",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password(test_environment):
    client, data = test_environment

    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_unknown_user(test_environment):
    client, data = test_environment

    response = client.post(
        "/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 401


def test_login_with_inactive_account(test_environment):
    client, data = test_environment

    db = TestingSessionLocal()

    try:
        user = db.query(User).filter(
            User.id == data["admin_id"]
        ).first()

        assert user is not None

        user.is_active = False
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"


def test_get_current_user_profile(test_environment):
    client, data = test_environment

    response = client.get(
        "/auth/me",
        headers=make_headers(data["admin_id"])
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["id"] == data["admin_id"]
    assert profile["username"] == "test_admin"
    assert profile["email"] == "admin@example.com"
    assert profile["role_name"] == "Admin"
    assert profile["is_active"] is True


def test_get_current_user_profile_without_token(test_environment):
    client, data = test_environment

    response = client.get("/auth/me")

    assert response.status_code == 401
