from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.user import User
from app.schemas.centre_test import (
    CentreTestCreate,
    CentreTestResponse,
    CentreTestUpdate,
)
from app.models.centre_staff import CentreStaff
from app.schemas.common import Page

router = APIRouter(
    prefix="/centre-tests",
    tags=["Centre Tests"],
)


def _can_manage_centre(db: Session, user: User, centre_id: UUID) -> bool:
    if user.role == "admin":
        return True
    return user.role == "staff" and db.query(CentreStaff.id).filter(
        CentreStaff.centre_id == centre_id,
        CentreStaff.user_id == user.id,
    ).first() is not None


@router.get("", response_model=Page[CentreTestResponse])
def list_centre_tests(
    centre_id: UUID | None = Query(default=None),
    test_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(CentreTest).join(DiagnosticCentre).join(DiagnosticTest).filter(
        CentreTest.is_available.is_(True),
        DiagnosticCentre.is_active.is_(True),
        DiagnosticTest.is_active.is_(True),
    )
    if centre_id:
        query = query.filter(CentreTest.centre_id == centre_id)
    if test_id:
        query = query.filter(CentreTest.test_id == test_id)
    total = query.count()
    return {"items": query.order_by(CentreTest.price.asc()).offset(offset).limit(limit).all(), "total": total, "offset": offset, "limit": limit}


@router.post(
    "",
    response_model=CentreTestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_centre_test(
    mapping_data: CentreTestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in {"admin", "staff"}:
        raise HTTPException(status_code=403, detail="Centre staff role required")
    if not _can_manage_centre(db, current_user, mapping_data.centre_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this centre")
    centre = db.get(DiagnosticCentre, mapping_data.centre_id)

    if centre is None or not centre.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    test = db.get(DiagnosticTest, mapping_data.test_id)

    if test is None or not test.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    existing_mapping = (
        db.query(CentreTest)
        .filter(
            CentreTest.centre_id == mapping_data.centre_id,
            CentreTest.test_id == mapping_data.test_id,
        )
        .first()
    )

    if existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This test is already mapped to the diagnostic centre",
        )

    centre_test = CentreTest(
        centre_id=mapping_data.centre_id,
        test_id=mapping_data.test_id,
        price=mapping_data.price,
    )

    db.add(centre_test)
    db.commit()
    db.refresh(centre_test)

    return centre_test


@router.patch(
    "/{centre_test_id}",
    response_model=CentreTestResponse,
)
def update_centre_test(
    centre_test_id: UUID,
    mapping_data: CentreTestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in {"admin", "staff"}:
        raise HTTPException(status_code=403, detail="Centre staff role required")
    centre_test = db.get(CentreTest, centre_test_id)

    if centre_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre test not found",
        )

    if not _can_manage_centre(db, current_user, centre_test.centre_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this centre")

    update_data = mapping_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(centre_test, field, value)

    db.commit()
    db.refresh(centre_test)

    return centre_test
