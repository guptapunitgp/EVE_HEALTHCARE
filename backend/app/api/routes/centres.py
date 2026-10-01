
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.api.permissions import require_role
from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.user import User
from app.models.centre_staff import CentreStaff
from app.schemas.diagnostic_centre import (
    DiagnosticCentreCreate,
    DiagnosticCentreResponse,
    DiagnosticCentreUpdate,
    NearbyCentreResponse,
)
from app.services.geo import haversine_km
from app.schemas.common import Page
from app.schemas.staff import CentreStaffResponse, StaffAssignRequest

router = APIRouter(
    prefix="/centres",
    tags=["Diagnostic Centres"],
)

def centres_cache_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response: Response = None,
    args: tuple = (),
    kwargs: dict = None,
) -> str:
    query = str(request.query_params) if request is not None else ""
    return f"{namespace}:centres:{query}"


@router.post(
    "",
    response_model=DiagnosticCentreResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_centre(
    centre_data: DiagnosticCentreCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    centre = DiagnosticCentre(**centre_data.model_dump())

    db.add(centre)
    db.commit()
    db.refresh(centre)

    await FastAPICache.clear()

    return centre


@router.get(
    "",
    response_model=Page[DiagnosticCentreResponse],
)
@cache(
    expire=60,
    key_builder=centres_cache_key_builder,
)
def list_centres(
    q: str | None = Query(default=None, max_length=120),
    city: str | None = Query(default=None, max_length=100),
    service: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(DiagnosticCentre).filter(DiagnosticCentre.is_active.is_(True))
    if city:
        query = query.filter(DiagnosticCentre.city.ilike(f"%{city.strip()}%"))
    results = query.order_by(DiagnosticCentre.name.asc()).all()
    if q:
        key = q.strip().casefold()
        results = [c for c in results if key in c.name.casefold() or key in c.city.casefold() or key in c.address.casefold() or any(key in str(s).casefold() for s in (c.services or []))]
    if service:
        key = service.casefold()
        results = [c for c in results if any(key in str(s).casefold() for s in (c.services or []))]
    return {"items": results[offset:offset + limit], "total": len(results), "offset": offset, "limit": limit}


@router.get(
    "/nearby",
    response_model=Page[NearbyCentreResponse],
)
def get_nearby_centres(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    centres = (
        db.query(DiagnosticCentre)
        .filter(
            DiagnosticCentre.is_active.is_(True),
            DiagnosticCentre.latitude.is_not(None),
            DiagnosticCentre.longitude.is_not(None),
        )
        .all()
    )

    nearby = []

    for centre in centres:
        distance = haversine_km(latitude, longitude, centre.latitude, centre.longitude)

        if distance <= radius_km:
            nearby.append(
                NearbyCentreResponse(
                    id=centre.id,
                    name=centre.name,
                    address=centre.address,
                    city=centre.city,
                    latitude=centre.latitude,
                    longitude=centre.longitude,
                    phone=centre.phone,
                    is_active=centre.is_active,
                    distance_km=round(distance, 2),
                )
            )

    nearby.sort(key=lambda centre: centre.distance_km)

    return {"items": nearby[offset:offset + limit], "total": len(nearby), "offset": offset, "limit": limit}


@router.get(
    "/{centre_id}",
    response_model=DiagnosticCentreResponse,
)
def get_centre(
    centre_id: UUID,
    db: Session = Depends(get_db),
):
    centre = db.get(DiagnosticCentre, centre_id)

    if centre is None or not centre.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    return centre


@router.patch(
    "/{centre_id}",
    response_model=DiagnosticCentreResponse,
)
async def update_centre(
    centre_id: UUID,
    centre_data: DiagnosticCentreUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in {"admin", "staff"}:
        raise HTTPException(status_code=403, detail="Centre staff role required")
    centre = db.get(DiagnosticCentre, centre_id)

    if centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    assigned = db.query(CentreStaff.id).filter(CentreStaff.centre_id == centre_id, CentreStaff.user_id == current_user.id).first()
    if current_user.role != "admin" and not assigned:
        raise HTTPException(status_code=403, detail="Not authorized to manage this centre")

    update_data = centre_data.model_dump(exclude_unset=True)
    if current_user.role != "admin" and "is_active" in update_data:
        raise HTTPException(status_code=403, detail="Only administrators can activate or deactivate a centre")

    for field, value in update_data.items():
        setattr(centre, field, value)

    db.commit()
    db.refresh(centre)

    await FastAPICache.clear()

    return centre


@router.get("/{centre_id}/staff", response_model=list[CentreStaffResponse])
def list_centre_staff(
    centre_id: UUID,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CentreStaff, User)
        .join(User, User.id == CentreStaff.user_id)
        .filter(CentreStaff.centre_id == centre_id)
        .order_by(User.email)
        .all()
    )
    return [{"id": membership.id, "centre_id": membership.centre_id, "user_id": user.id, "email": user.email, "full_name": user.full_name} for membership, user in rows]


@router.post("/{centre_id}/staff", response_model=CentreStaffResponse, status_code=status.HTTP_201_CREATED)
def assign_centre_staff(
    centre_id: UUID,
    data: StaffAssignRequest,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    centre = db.get(DiagnosticCentre, centre_id)
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if centre is None or user is None:
        raise HTTPException(status_code=404, detail="Centre or user not found")
    if user.role == "admin":
        raise HTTPException(status_code=409, detail="Administrators do not need centre assignments")
    existing = db.query(CentreStaff).filter(CentreStaff.centre_id == centre_id, CentreStaff.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already assigned to this centre")
    assignment = CentreStaff(centre_id=centre_id, user_id=user.id)
    user.role = "staff"
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return {"id": assignment.id, "centre_id": assignment.centre_id, "user_id": user.id, "email": user.email, "full_name": user.full_name}


@router.delete("/{centre_id}/staff/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_centre_staff(
    centre_id: UUID,
    user_id: UUID,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    assignment = db.query(CentreStaff).filter(CentreStaff.centre_id == centre_id, CentreStaff.user_id == user_id).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Staff assignment not found")
    db.delete(assignment)
    db.flush()
    user = db.get(User, user_id)
    if user and user.role == "staff" and not db.query(CentreStaff.id).filter(CentreStaff.user_id == user_id).first():
        user.role = "patient"
    db.commit()
    return None
