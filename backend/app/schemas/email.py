from pydantic import BaseModel


class SendEmailResponse(BaseModel):
    lead_id: str
    status: str
    message: str

