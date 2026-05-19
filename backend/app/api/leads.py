from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.lead import Lead, OptOut
from backend.app.models.user import User
from backend.app.schemas.leads import LeadRead, LeadStatusUpdate, OptOutRequest
from backend.app.services.serializers import lead_to_read

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
def list_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[LeadRead]:
    statement = select(Lead).where(Lead.user_id == current_user.id)
    if status:
        statement = statement.where(Lead.email_status == status)
    statement = statement.order_by(desc(Lead.created_at)).limit(limit)
    return [lead_to_read(lead) for lead in db.scalars(statement).all()]


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadRead:
    lead = db.get(Lead, lead_id)
    if not lead or lead.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead_to_read(lead)


@router.patch("/{lead_id}/status", response_model=LeadRead)
def update_status(
    lead_id: str,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadRead:
    lead = db.get(Lead, lead_id)
    if not lead or lead.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.email_status = payload.email_status
    db.commit()
    db.refresh(lead)
    return lead_to_read(lead)


@router.post("/opt-out", status_code=201)
def add_opt_out(
    payload: OptOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    normalized = payload.email.strip().lower()
    existing = db.scalar(select(OptOut).where(OptOut.email == normalized))
    if not existing:
        db.add(OptOut(email=normalized, reason=payload.reason))
    for lead in db.scalars(
        select(Lead).where(Lead.user_id == current_user.id, func.lower(Lead.email) == normalized)
    ):
        lead.email_status = "opted_out"
    db.commit()
    return {"message": "Opt-out recorded"}
