from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.models.lead import Lead, OptOut, OutreachLog
from backend.app.models.user import User
from backend.app.schemas.email import SendEmailResponse
from sender.smtp_sender import SmtpOutreachSender

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/send/{lead_id}", response_model=SendEmailResponse)
def send_lead_email(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendEmailResponse:
    settings = get_settings()
    if not settings.email_sending_enabled:
        raise HTTPException(
            status_code=403,
            detail="Email sending is disabled. Set EMAIL_SENDING_ENABLED=true only after consent and review.",
        )

    lead = db.get(Lead, lead_id)
    if not lead or lead.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.email:
        raise HTTPException(status_code=400, detail="This lead has no public email address")

    normalized_email = lead.email.strip().lower()
    if db.scalar(select(OptOut).where(OptOut.email == normalized_email)):
        lead.email_status = "opted_out"
        db.commit()
        raise HTTPException(status_code=400, detail="Recipient has opted out")

    sender = SmtpOutreachSender()
    try:
        result = sender.send(
            to_email=normalized_email,
            subject=lead.generated_email_subject or f"Website idea for {lead.business_name}",
            body=lead.generated_email_body or "",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    lead.email_status = "sent"
    db.add(
        OutreachLog(
            lead_id=lead.id,
            user_id=current_user.id,
            status="sent",
            message=f"Email sent to {normalized_email}",
            provider_message_id=result.provider_message_id,
        )
    )
    db.commit()
    return SendEmailResponse(lead_id=lead.id, status="sent", message="Email sent and logged")
