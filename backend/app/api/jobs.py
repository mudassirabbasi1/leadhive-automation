import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.jobs import LeadSearchRequest, LeadSearchResponse
from backend.app.services.lead_pipeline import LeadPipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)


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
    except Exception as exc:
        logger.exception("Lead search failed")
        raise HTTPException(
            status_code=502,
            detail="Lead search failed while contacting public data sources. Please retry in a moment.",
        ) from exc

    message = (
        f"Created {created} draft outreach leads."
        if created
        else "No qualified leads found with a public email and website score below 70."
    )
    return LeadSearchResponse(batch_id=batch_id, created=created, message=message)
