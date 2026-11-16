
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_role,
    is_super_admin
)
from app.core.security import hash_password
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.schemas.user import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


# ==========================================
# Helper 1: Get Target User
# Super Admin: Global access
# Admin / Analyst: Own company only
# ==========================================

def get_target_user(
    user_id: int,
    db: Session,
    current_user: User
):
    query = db.query(User).filter(
        User.id == user_id
    )

    if not is_super_admin(current_user, db):
        query = query.filter(
            User.company_id == current_user.company_id
        )

    user = query.first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# ==========================================
# Helper 2: Protect Super Admin Accounts
# ==========================================

def protect_super_admin_target(
    target_user: User,
    current_user: User,
    db: Session
):
    target_is_super_admin = is_super_admin(
        target_user,
        db
    )

    current_is_super_admin = is_super_admin(
        current_user,
        db
    )

    if target_is_super_admin and not current_is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can manage Super Admin accounts"
        )


# ==========================================
# 1. Register New User
# Admin: Own Company
# Super Admin: Any Existing Company
# ==========================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    super_admin = is_super_admin(
        current_user,
        db
    )

    # Determine target company
    if super_admin:
        target_company_id = user_data.company_id
    else:
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

    # Check duplicate username
    existing_username = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # Check duplicate email
    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    # Verify requested role
    role = db.query(Role).filter(
        Role.id == user_data.role_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Ordinary Admin cannot assign Admin or Super Admin
    if (
        not super_admin
        and role.name in ("Admin", "Super Admin")
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot assign this role"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(
            user_data.password
        ),
        company_id=target_company_id,
        role_id=user_data.role_id,
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create user"
        )

    return new_user


# ==========================================
# 2. Get All Users
# Admin / Analyst: Own Company
# Super Admin: All Companies
# ==========================================

@router.get(
    "/",
    response_model=list[UserResponse]
)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    query = db.query(User)

    if not is_super_admin(current_user, db):
        query = query.filter(
            User.company_id == current_user.company_id
        )

    return query.order_by(User.id).all()


# ==========================================
# 3. Get User by ID
# ==========================================

@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    return get_target_user(
        user_id,
        db,
        current_user
    )


# ==========================================
# 4. Update User
# Admin: Own Company
# Super Admin: All Companies
# ==========================================

@router.put(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    super_admin = is_super_admin(
        current_user,
        db
    )

    user = get_target_user(
        user_id,
        db,
        current_user
    )

    protect_super_admin_target(
        user,
        current_user,
        db
    )

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    # Validate requested role
    if "role_id" in update_data:

        role = db.query(Role).filter(
            Role.id == update_data["role_id"]
        ).first()

        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found"
            )

        # Ordinary Admin cannot assign privileged roles
        if (
            not super_admin
            and role.name in ("Admin", "Super Admin")
        ):
            raise HTTPException(
                status_code=403,
                detail="You cannot assign this role"
            )

        target_role = db.query(Role).filter(
            Role.id == user.role_id
        ).first()

        # Protect last active Super Admin from demotion
        if (
            super_admin
            and is_super_admin(user, db)
            and role.name != "Super Admin"
        ):
            active_super_admins = db.query(User).join(
                Role,
                User.role_id == Role.id
            ).filter(
                User.is_active.is_(True),
                Role.name == "Super Admin"
            ).count()

            if active_super_admins <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last active Super Admin"
                )

        # Protect last active Admin in the company
        if (
            target_role
            and target_role.name == "Admin"
            and role.name != "Admin"
        ):
            active_admins = db.query(User).join(
                Role,
                User.role_id == Role.id
            ).filter(
                User.company_id == user.company_id,
                User.is_active.is_(True),
                Role.name == "Admin"
            ).count()

            if active_admins <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last active Admin in this company"
                )

    # Check duplicate username
    if "username" in update_data:

        if update_data["username"] is None:
            raise HTTPException(
                status_code=422,
                detail="Username cannot be null"
            )

        existing_username = db.query(User).filter(
            User.username == update_data["username"],
            User.id != user_id
        ).first()

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

    # Check duplicate email
    if "email" in update_data:

        if update_data["email"] is None:
            raise HTTPException(
                status_code=422,
                detail="Email cannot be null"
            )

        existing_email = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

    # Hash password before saving
    if "password" in update_data:

        if update_data["password"] is None:
            raise HTTPException(
                status_code=422,
                detail="Password cannot be null"
            )

        update_data["hashed_password"] = hash_password(
            update_data.pop("password")
        )

    # Only explicitly allowed fields can be updated
    allowed_fields = {
        "username",
        "email",
        "role_id",
        "hashed_password"
    }

    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(user, key, value)

    try:
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update user"
        )

    return user


# ==========================================
# 5. Delete User (Soft Delete)
# Admin: Own Company
# Super Admin: All Companies
# ==========================================

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    )
):
    super_admin = is_super_admin(
        current_user,
        db
    )

    user = get_target_user(
        user_id,
        db,
        current_user
    )

    protect_super_admin_target(
        user,
        current_user,
        db
    )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="User is already inactive"
        )

    target_role = db.query(Role).filter(
        Role.id == user.role_id
    ).first()

    # Protect last active Admin in the company
    if target_role and target_role.name == "Admin":

        active_admins = db.query(User).join(
            Role,
            User.role_id == Role.id
        ).filter(
            User.company_id == user.company_id,
            User.is_active.is_(True),
            Role.name == "Admin"
        ).count()

        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last active Admin"
            )

    # Protect last active Super Admin globally
    if target_role and target_role.name == "Super Admin":

        if not super_admin:
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can deactivate this account"
            )

        active_super_admins = db.query(User).join(
            Role,
            User.role_id == Role.id
        ).filter(
            User.is_active.is_(True),
            Role.name == "Super Admin"
        ).count()

        if active_super_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last active Super Admin"
            )

    # Prevent deleting own account
    if user.id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot deactivate your own account"
        )

    # Soft delete: preserve user and historical records
    user.is_active = False

    try:
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not deactivate user"
        )

    return {
        "message": "User deactivated successfully",
        "user_id": user.id,
        "is_active": user.is_active
    }
