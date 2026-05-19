import json
from typing import Any

from backend.app.models.lead import Lead
from backend.app.schemas.leads import LeadRead


def parse_issues(raw: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def lead_to_read(lead: Lead) -> LeadRead:
    return LeadRead(
        id=lead.id,
        batch_id=lead.batch_id,
        city=lead.city,
        niche=lead.niche,
        business_name=lead.business_name,
        website=lead.website,
        email=lead.email,
        phone=lead.phone,
        address=lead.address,
        source_url=lead.source_url,
        quality_score=lead.quality_score,
        issues=parse_issues(lead.issues_json),
        generated_email_subject=lead.generated_email_subject,
        generated_email_body=lead.generated_email_body,
        email_status=lead.email_status,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )

