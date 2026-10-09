from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.certificate import CertificateStatus

class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    recipient_identifier: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    status: CertificateStatus
    certificate_code: Optional[str] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VerificationResponse(BaseModel):
    valid: bool
    certificate_code: Optional[str] = None
    recipient_name: Optional[str] = None
    course_or_event: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    generated_at: Optional[datetime] = None
    message: str
