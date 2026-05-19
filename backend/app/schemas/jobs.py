from pydantic import BaseModel, Field


class LeadSearchRequest(BaseModel):
    city: str = Field(min_length=2, max_length=120)
    niche: str = Field(min_length=2, max_length=120)
    limit: int = Field(default=15, ge=1, le=50)


class LeadSearchResponse(BaseModel):
    batch_id: str
    created: int
    message: str

