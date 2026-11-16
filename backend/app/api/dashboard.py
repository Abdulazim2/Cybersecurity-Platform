from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_role,
    is_super_admin
)

from app.models.user import User
from app.services.dashboard_service import get_dashboard_statistics
from app.schemas.dashboard import DashboardResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/statistics",
    response_model=DashboardResponse
)
def get_dashboard(
    hours: int | None = Query(
        default=None,
        ge=0,
        le=8760,
        description="Time range in hours. 0 or omitted means all time."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    # Super Admin receives platform-wide statistics.
    # Other users receive statistics for their own company.
    target_company_id = None

    if not is_super_admin(current_user, db):
        target_company_id = current_user.company_id

    statistics = get_dashboard_statistics(
        db=db,
        company_id=target_company_id,
        hours=hours
    )

    return statistics
