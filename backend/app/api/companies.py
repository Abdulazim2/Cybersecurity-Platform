from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


# ============================================================
# CURRENT USER COMPANY
# ============================================================

@router.get("/me", response_model=CompanyResponse)
def get_my_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    company = db.query(Company).filter(
        Company.id == current_user.company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company


@router.put("/me", response_model=CompanyResponse)
def update_my_company(
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    company = db.query(Company).filter(
        Company.id == current_user.company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    update_data = company_data.model_dump(exclude_unset=True)

    if update_data.get("name") is None and "name" in update_data:
        raise HTTPException(
            status_code=422,
            detail="Company name cannot be null"
        )

    if "name" in update_data:
        existing_company = db.query(Company).filter(
            Company.name == update_data["name"],
            Company.id != company.id
        ).first()

        if existing_company:
            raise HTTPException(
                status_code=409,
                detail="Company name already exists"
            )

    for key, value in update_data.items():
        setattr(company, key, value)

    try:
        db.commit()
        db.refresh(company)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Company update conflicts with existing data"
        )

    return company


# ============================================================
# SUPER ADMIN - GLOBAL COMPANY MANAGEMENT
# ============================================================

@router.get("/", response_model=list[CompanyResponse])
def list_all_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Super Admin")
    )
):
    return db.query(Company).order_by(Company.id).all()


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Super Admin")
    )
):
    existing_company = db.query(Company).filter(
        Company.name == company_data.name
    ).first()

    if existing_company:
        raise HTTPException(
            status_code=409,
            detail="Company name already exists"
        )

    company = Company(
        name=company_data.name,
        industry=company_data.industry,
        email=company_data.email
    )

    try:
        db.add(company)
        db.commit()
        db.refresh(company)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Company already exists"
        )

    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Super Admin")
    )
):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Super Admin")
    )
):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    update_data = company_data.model_dump(exclude_unset=True)

    if update_data.get("name") is None and "name" in update_data:
        raise HTTPException(
            status_code=422,
            detail="Company name cannot be null"
        )

    if "name" in update_data:
        existing_company = db.query(Company).filter(
            Company.name == update_data["name"],
            Company.id != company.id
        ).first()

        if existing_company:
            raise HTTPException(
                status_code=409,
                detail="Company name already exists"
            )

    for key, value in update_data.items():
        setattr(company, key, value)

    try:
        db.commit()
        db.refresh(company)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Company update conflicts with existing data"
        )

    return company
