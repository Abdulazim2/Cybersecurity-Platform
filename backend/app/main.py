
from fastapi import FastAPI
from datetime import datetime, timezone
from app.database.connection import test_database_connection

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.companies import router as companies_router
from app.api.factories import router as factories_router
from app.api.network_events import router as network_events_router
from app.api.data_upload import router as data_upload_router
from app.api.predictions import router as predictions_router
from app.api.dashboard import router as dashboard_router
from app.api.roles import router as roles_router
from app.api.sensors import router as sensors_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Cybersecurity Monitoring Platform",
    description="Backend API for Industrial Cybersecurity Monitoring",
    version="1.0.0"
)
# Configure CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Authentication routes
app.include_router(auth_router)

# Register Users routes
app.include_router(users_router)

# Register Companies routes
app.include_router(companies_router)

# Register Factories routes
app.include_router(factories_router)
app.include_router(sensors_router)
app.include_router(network_events_router)
app.include_router(data_upload_router)
app.include_router(predictions_router)
app.include_router(dashboard_router)
app.include_router(roles_router)

@app.get("/")
def home():
    return {
        "message": "Cybersecurity Platform Backend is Running",
        "status": "Online"
    }


@app.get("/health")
def health_check():
    database_status = "Connected"

    try:
        test_database_connection()
    except Exception:
        database_status = "Disconnected"

    overall_status = (
        "Healthy" if database_status == "Connected" else "Degraded"
    )

    return {
        "status": overall_status,
        "service": "Backend API",
        "database": database_status,
        "last_check": datetime.now(timezone.utc).isoformat()
    }

from app.api.notifications import router as notifications_router

app.include_router(notifications_router)

from app.api.ml import router as ml_router
app.include_router(ml_router)
