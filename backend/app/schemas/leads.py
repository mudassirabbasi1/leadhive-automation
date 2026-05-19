from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LeadRead(BaseModel):
    id: str
    batch_id: str
    city: str
    niche: str
    business_name: str
    website: str | None
    email: str | None
    phone: str | None
    address: str | None
    source_url: str | None
    quality_score: float
    issues: list[dict[str, Any]]
    generated_email_subject: str | None
    generated_email_body: str | None
    email_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    email_status: str = Field(pattern="^(draft|sent|replied|bounced|opted_out)$")


class OptOutRequest(BaseModel):
    email: str
    reason: str | None = None

