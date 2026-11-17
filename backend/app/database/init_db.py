from app.database.connection import Base, engine

from app.models.company import Company
from app.models.factory import Factory
from app.models.factory_sensor import FactorySensor
from app.models.role import Role
from app.models.user import User
from app.models.network_event import NetworkEvent
from app.models.uploaded_dataset import UploadedDataset
from app.models.prediction import Prediction
from app.models.notification import Notification, NotificationRead


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
