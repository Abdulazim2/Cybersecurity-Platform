from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.dependencies import get_db, require_role, is_super_admin
from app.models.user import User
from app.models.factory import Factory
from app.models.uploaded_dataset import UploadedDataset
from app.services.data_ingestion_service import process_uploaded_file


router = APIRouter(
    prefix="/data-upload",
    tags=["Data Upload"]
)


def get_target_factory(
    factory_id: int,
    db: Session,
    current_user: User
):
    """
    Super Admin can access factories across all companies.
    Other users can access active factories in their own company only.
    """

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found"
        )

    return factory


def get_dataset_query(
    db: Session,
    current_user: User
):
    """
    Return a company-scoped query for normal users,
    or a global query for Super Admin.
    """

    query = db.query(UploadedDataset)

    if not is_super_admin(current_user, db):
        query = query.filter(
            UploadedDataset.company_id == current_user.company_id
        )

    return query


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    factory_id: int = Form(...),
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    try:
        # 1. Find an active factory that the user is allowed to access.
        factory = get_target_factory(
            factory_id=factory_id,
            db=db,
            current_user=current_user
        )

        # 2. Read the uploaded file (maximum 10 MB + 1 byte for validation).
        content = await file.read(10 * 1024 * 1024 + 1)

        # 3. Validate and process the file.
        result = process_uploaded_file(
            filename=file.filename or "",
            file_content=content,
            dataset_type=dataset_type
        )

        # 4. Always use the factory's company.
        # This is important for Super Admin uploading to another company.
        uploaded_dataset = UploadedDataset(
            company_id=factory.company_id,
            factory_id=factory.id,
            uploaded_by=current_user.id,
            dataset_type=result["dataset_type"],
            filename=result["filename"],
            records_count=result["records_count"],
            columns=result["columns"],
            records=result["records"]
        )

        # 5. Save the dataset.
        db.add(uploaded_dataset)
        db.commit()
        db.refresh(uploaded_dataset)

        return {
            "message": "Dataset uploaded and saved successfully",
            "dataset_id": uploaded_dataset.id,
            "company_id": uploaded_dataset.company_id,
            "factory_id": uploaded_dataset.factory_id,
            "factory_name": factory.name,
            "uploaded_by": uploaded_dataset.uploaded_by,
            "dataset_type": uploaded_dataset.dataset_type,
            "filename": uploaded_dataset.filename,
            "records_count": uploaded_dataset.records_count,
            "columns": uploaded_dataset.columns,
            "records": uploaded_dataset.records,
            "created_at": uploaded_dataset.created_at
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while saving dataset"
        )

    finally:
        await file.close()


@router.get("/")
def get_uploaded_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    datasets = get_dataset_query(
        db=db,
        current_user=current_user
    ).order_by(
        UploadedDataset.created_at.desc()
    ).all()

    return [
        {
            "dataset_id": dataset.id,
            "company_id": dataset.company_id,
            "factory_id": dataset.factory_id,
            "uploaded_by": dataset.uploaded_by,
            "dataset_type": dataset.dataset_type,
            "filename": dataset.filename,
            "records_count": dataset.records_count,
            "created_at": dataset.created_at
        }
        for dataset in datasets
    ]


@router.get("/{dataset_id}")
def get_uploaded_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Security Analyst")
    )
):
    dataset = get_dataset_query(
        db=db,
        current_user=current_user
    ).filter(
        UploadedDataset.id == dataset_id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    return {
        "dataset_id": dataset.id,
        "company_id": dataset.company_id,
        "factory_id": dataset.factory_id,
        "uploaded_by": dataset.uploaded_by,
        "dataset_type": dataset.dataset_type,
        "filename": dataset.filename,
        "records_count": dataset.records_count,
        "columns": dataset.columns,
        "records": dataset.records,
        "created_at": dataset.created_at
    }
