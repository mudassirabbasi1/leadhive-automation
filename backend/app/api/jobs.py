from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.jobs import LeadSearchRequest, LeadSearchResponse
from backend.app.services.lead_pipeline import LeadPipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/search", response_model=LeadSearchResponse)
def create_lead_search(
    payload: LeadSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadSearchResponse:
    try:
        batch_id, created = LeadPipeline().run(
            db=db,
            user=current_user,
            city=payload.city,
            niche=payload.niche,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LeadSearchResponse(
        batch_id=batch_id,
        created=created,
        message=f"Created {created} draft outreach leads.",
    )

