
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_role,
    is_super_admin
)

from app.models.user import User
from app.models.factory import Factory
from app.models.company import Company

from app.schemas.factory import (
    FactoryCreate,
    FactoryUpdate,
    FactoryResponse
)


router = APIRouter(
    prefix="/factories",
    tags=["Factories"]
)


# ==========================================
# Helper: Get Factory
# Super Admin: Global access
# Admin / Analyst: Own company only
# ==========================================

def get_target_factory(
    factory_id: int,
    db: Session,
    current_user: User
):
    query = db.query(Factory).filter(
        Factory.id == factory_id,
        Factory.is_active.is_(True)
    )

    if not is_super_admin(current_user, db):
        query = query.filter(
            Factory.company_id == current_user.company_id
        )

    factory = query.first()

    if not factory:
        raise HTTPException(
            status_code=404,
            detail="Factory not found"
        )

    return factory


# ==========================================
# 1. Create Factory
# Admin: Own company
# Super Admin: Any existing company
# ==========================================

@router.post(
    "/",
    response_model=FactoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_factory(
    factory_data: FactoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    super_admin = is_super_admin(
        current_user,
        db
    )

    # Determine target company
    if super_admin:

        if factory_data.company_id is None:
            raise HTTPException(
                status_code=422,
                detail="company_id is required for Super Admin"
            )

        target_company_id = factory_data.company_id

    else:
        # Admin cannot choose another company
        target_company_id = current_user.company_id

    # Verify company exists
    company = db.query(Company).filter(
        Company.id == target_company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    new_factory = Factory(
        name=factory_data.name,
        location=factory_data.location,
        company_id=target_company_id,
        is_active=True
    )

    try:
        db.add(new_factory)
        db.commit()
        db.refresh(new_factory)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create factory"
        )

    return new_factory


# ==========================================
# 2. Get All Active Factories
# Admin / Analyst: Own company
# Super Admin: All companies
# ==========================================

@router.get(
    "/",
    response_model=list[FactoryResponse]
)
def get_factories(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    query = db.query(Factory).filter(
        Factory.is_active.is_(True)
    )

    if not is_super_admin(current_user, db):
        query = query.filter(
            Factory.company_id == current_user.company_id
        )

    return query.order_by(Factory.id).all()


# ==========================================
# 3. Get Factory by ID
# ==========================================

@router.get(
    "/{factory_id}",
    response_model=FactoryResponse
)
def get_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    return get_target_factory(
        factory_id,
        db,
        current_user
    )


# ==========================================
# 4. Update Factory
# Admin: Own company
# Super Admin: All companies
# ==========================================

@router.put(
    "/{factory_id}",
    response_model=FactoryResponse
)
def update_factory(
    factory_id: int,
    factory_data: FactoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    factory = get_target_factory(
        factory_id,
        db,
        current_user
    )

    update_data = factory_data.model_dump(
        exclude_unset=True
    )

    # Reject empty update requests
    if not update_data:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided for update"
        )

    # Do not allow null values for required name
    if (
        "name" in update_data
        and update_data["name"] is None
    ):
        raise HTTPException(
            status_code=422,
            detail="Factory name cannot be null"
        )

    # Only update allowed fields
    allowed_fields = {
        "name",
        "location"
    }

    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(factory, key, value)

    try:
        db.commit()
        db.refresh(factory)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update factory"
        )

    return factory


# ==========================================
# 5. Delete Factory (Soft Delete)
# Admin: Own company
# Super Admin: All companies
# ==========================================

@router.delete("/{factory_id}")
def delete_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    factory = get_target_factory(
        factory_id,
        db,
        current_user
    )

    # Soft delete: preserve historical records
    factory.is_active = False

    try:
        db.commit()
        db.refresh(factory)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not deactivate factory"
        )

    return {
        "message": "Factory deactivated successfully",
        "factory_id": factory.id,
        "is_active": factory.is_active
    }
