from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.permissions import require_role
from app.db.database import get_db
from app.models.diagnostic_test import DiagnosticTest
from app.models.user import User
from app.schemas.diagnostic_test import (
    DiagnosticTestCreate,
    DiagnosticTestResponse,
    DiagnosticTestUpdate,
)
from app.schemas.common import Page
router = APIRouter(
    prefix="/tests",
    tags=["Diagnostic Tests"],
)


@router.post(
    "",
    response_model=DiagnosticTestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test(
    test_data: DiagnosticTestCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    diagnostic_test = DiagnosticTest(
        name=test_data.name,
        description=test_data.description,
        preparation_instructions=test_data.preparation_instructions,
        duration_minutes=test_data.duration_minutes,
        category=test_data.category,
        sample_type=test_data.sample_type,
        estimated_report_time_minutes=test_data.estimated_report_time_minutes,
    )

    db.add(diagnostic_test)
    db.commit()
    db.refresh(diagnostic_test)

    return diagnostic_test


@router.get(
    "",
    response_model=Page[DiagnosticTestResponse],
)
def list_tests(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(DiagnosticTest).filter(DiagnosticTest.is_active.is_(True))
    if q:
        query = query.filter(DiagnosticTest.name.ilike(f"%{q.strip()}%"))
    if category:
        query = query.filter(DiagnosticTest.category.ilike(f"%{category.strip()}%"))
    total = query.count()
    tests = query.order_by(DiagnosticTest.name.asc()).offset(offset).limit(limit).all()
    return {"items": tests, "total": total, "offset": offset, "limit": limit}

@router.get(
    "/{test_id}",
    response_model=DiagnosticTestResponse,
)
def get_test(
    test_id: UUID,
    db: Session = Depends(get_db),
):
    diagnostic_test = db.get(DiagnosticTest, test_id)

    if diagnostic_test is None or not diagnostic_test.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    return diagnostic_test

@router.patch(
    "/{test_id}",
    response_model=DiagnosticTestResponse,
)
def update_test(
    test_id: UUID,
    test_data: DiagnosticTestUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    diagnostic_test = db.get(DiagnosticTest, test_id)

    if diagnostic_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    update_data = test_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(diagnostic_test, field, value)

    db.commit()
    db.refresh(diagnostic_test)

    return diagnostic_test
