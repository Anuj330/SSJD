from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeCreate, SchemeUpdate


def create_scheme(
    payload: SchemeCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    existing = db.query(Scheme).filter(Scheme.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Scheme name already exists")

    scheme = Scheme(
        name=payload.name,
        scheme_type=payload.scheme_type,
        description=payload.description,
        interest_rate=payload.interest_rate,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        tenure_months=payload.tenure_months,
        compounding=payload.compounding,
        premature_penalty_pct=payload.premature_penalty_pct,
    )
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return _scheme_dict(scheme)


def list_schemes(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    query = db.query(Scheme).order_by(Scheme.id)
    # Members only see active schemes
    if current.role == "member":
        query = query.filter(Scheme.is_active == True)
    schemes = query.all()
    return [_scheme_dict(s) for s in schemes]


def get_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    if current.role == "member" and not scheme.is_active:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return _scheme_dict(scheme)


def update_scheme(
    scheme_id: int,
    payload: SchemeUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != scheme.name:
        dup = db.query(Scheme).filter(Scheme.name == update_data["name"]).first()
        if dup:
            raise HTTPException(status_code=409, detail="Scheme name already exists")

    for field, value in update_data.items():
        setattr(scheme, field, value)

    db.commit()
    db.refresh(scheme)
    return _scheme_dict(scheme)


def _scheme_dict(scheme: Scheme) -> dict:
    return {
        "id": scheme.id,
        "name": scheme.name,
        "scheme_type": scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type),
        "description": scheme.description,
        "interest_rate": scheme.interest_rate,
        "min_amount": scheme.min_amount,
        "max_amount": scheme.max_amount,
        "tenure_months": scheme.tenure_months,
        "compounding": scheme.compounding.value if hasattr(scheme.compounding, "value") else str(scheme.compounding),
        "premature_penalty_pct": scheme.premature_penalty_pct,
        "is_active": scheme.is_active,
        "created_at": scheme.created_at,
    }
