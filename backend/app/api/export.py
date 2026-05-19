import io
import csv

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.lead import Lead
from backend.app.models.user import User
from backend.app.services.serializers import parse_issues

router = APIRouter(prefix="/export", tags=["export"])

try:
    import pandas as pd
except ImportError:  # pragma: no cover - local lightweight installs can skip Pandas.
    pd = None


@router.get("/leads.csv")
def export_leads_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    leads = db.scalars(select(Lead).where(Lead.user_id == current_user.id)).all()
    rows = [
        {
            "business_name": lead.business_name,
            "website": lead.website,
            "email": lead.email,
            "phone": lead.phone,
            "address": lead.address,
            "source_url": lead.source_url,
            "quality_score": lead.quality_score,
            "issues": "; ".join(issue.get("label", "") for issue in parse_issues(lead.issues_json)),
            "email_status": lead.email_status,
            "generated_email_subject": lead.generated_email_subject,
            "generated_email_body": lead.generated_email_body,
        }
        for lead in leads
    ]
    output = io.StringIO()
    if pd:
        pd.DataFrame(rows).to_csv(output, index=False)
    else:
        fieldnames = list(rows[0].keys()) if rows else [
            "business_name",
            "website",
            "email",
            "phone",
            "address",
            "source_url",
            "quality_score",
            "issues",
            "email_status",
            "generated_email_subject",
            "generated_email_body",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leadhive-leads.csv"'},
    )
