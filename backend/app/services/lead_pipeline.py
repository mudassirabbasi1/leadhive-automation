import json
import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from analyzer.website_analyzer import WebsiteAnalyzer
from backend.app.models.lead import Lead
from backend.app.models.user import User
from email_generator.generator import OutreachEmailGenerator
from scraper.public_sources import PublicBusinessScraper

logger = logging.getLogger(__name__)


class LeadPipeline:
    """Coordinates scraping, analysis, personalization, and persistence."""

    def __init__(self) -> None:
        self.scraper = PublicBusinessScraper()
        self.analyzer = WebsiteAnalyzer()
        self.email_generator = OutreachEmailGenerator()

    def run(self, db: Session, user: User, city: str, niche: str, limit: int) -> tuple[str, int]:
        batch_id = str(uuid4())
        # Pull extra public candidates because many listings do not publish email addresses.
        businesses = self.scraper.search(city=city, niche=niche, limit=min(limit * 5, 100))
        created = 0

        for business in businesses:
            if created >= limit:
                break
            if not business.email:
                logger.info("Skipping lead without public email", extra={"business": business.name})
                continue
            try:
                analysis = self.analyzer.analyze(business.website)
                if analysis.score >= 70:
                    logger.info(
                        "Skipping lead with acceptable website score",
                        extra={"business": business.name, "quality_score": analysis.score},
                    )
                    continue
                email = self.email_generator.generate(
                    business_name=business.name,
                    niche=niche,
                    city=city,
                    website=business.website,
                    issues=analysis.issues,
                    score=analysis.score,
                )
                lead = Lead(
                    user_id=user.id,
                    batch_id=batch_id,
                    city=city.strip(),
                    niche=niche.strip(),
                    business_name=business.name,
                    website=business.website,
                    email=business.email,
                    phone=business.phone,
                    address=business.address,
                    source_url=business.source_url,
                    quality_score=analysis.score,
                    issues_json=json.dumps([issue.model_dump() for issue in analysis.issues]),
                    generated_email_subject=email.subject,
                    generated_email_body=email.body,
                    email_status="draft",
                )
                db.add(lead)
                created += 1
            except Exception:
                logger.exception("Skipping lead after pipeline failure", extra={"business": business.name})

        db.commit()
        logger.info("Lead batch complete", extra={"batch_id": batch_id, "created_count": created})
        return batch_id, created
