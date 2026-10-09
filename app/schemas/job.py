from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.job import JobStatus
from app.schemas.recipient import RecipientInput
from app.schemas.certificate import CertificateResponse

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Python Mastery Bootcamp 2026"})
    issuer_name: Optional[str] = Field(default=None, max_length=255, json_schema_extra={"example": "AeroCloud Academy"})
    course_or_event: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Backend Engineering Course"})
    issue_date: str = Field(..., json_schema_extra={"example": "2026-10-10"})
    template_id: Optional[str] = Field(default="classic_gold", json_schema_extra={"example": "classic_gold"})
    send_email: Optional[bool] = Field(default=False, description="Send generated PDF certificates directly to recipient emails")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient records")

class JobStatusResponse(BaseModel):
    id: str
    title: str
    issuer_name: str
    course_or_event: str
    issue_date: str
    template_id: str = "classic_gold"
    send_email: bool = False
    status: JobStatus
    total_recipients: int
    processed_count: int
    successful_count: int
    failed_count: int
    progress_percentage: float
    error_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobResponse(JobStatusResponse):
    certificates: List[CertificateResponse] = []

    model_config = ConfigDict(from_attributes=True)

class JobSummaryResponse(BaseModel):
    job: JobStatusResponse
    successful_certificates: List[CertificateResponse]
    failed_certificates: List[CertificateResponse]
