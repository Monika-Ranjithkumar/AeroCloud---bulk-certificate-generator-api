from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.job import CertificateJob
from app.models.certificate import CertificateRecord, CertificateStatus
from app.schemas.job import JobCreateRequest, JobStatusResponse, JobResponse, JobSummaryResponse
from app.schemas.certificate import CertificateResponse
from app.services.job_processor import create_bulk_job, process_job_background, create_job_zip_archive

router = APIRouter()

def build_job_status_response(job: CertificateJob) -> JobStatusResponse:
    progress = 0.0
    if job.total_recipients > 0:
        progress = round((job.processed_count / job.total_recipients) * 100.0, 2)
    
    return JobStatusResponse(
        id=job.id,
        title=job.title,
        issuer_name=job.issuer_name,
        course_or_event=job.course_or_event,
        issue_date=job.issue_date,
        template_id=job.template_id or "classic_gold",
        send_email=job.send_email or False,
        status=job.status,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        progress_percentage=progress,
        error_summary=job.error_summary,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

def build_cert_response(cert: CertificateRecord) -> CertificateResponse:
    download_url = f"/api/v1/certificates/{cert.id}/download" if cert.status == CertificateStatus.GENERATED else None
    preview_url = f"/api/v1/certificates/{cert.id}/preview" if cert.status == CertificateStatus.GENERATED else None
    
    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        recipient_identifier=cert.recipient_identifier,
        custom_attributes=cert.custom_attributes,
        status=cert.status,
        certificate_code=cert.certificate_code,
        download_url=download_url,
        preview_url=preview_url,
        error_message=cert.error_message,
        email_sent=cert.email_sent or False,
        email_sent_at=cert.email_sent_at,
        generated_at=cert.generated_at,
        created_at=cert.created_at
    )

@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_certificate_job(
    request: Request,
    body: JobCreateRequest,
    background_tasks: BackgroundTasks,
    process_async: bool = Query(True, description="Process generation asynchronously in background"),
    db: Session = Depends(get_db)
):
    """
    Submit a bulk certificate generation job.
    Accepts a list of recipients and certificate details.
    """
    raw_json = await request.json()
    raw_recipients = raw_json.get("recipients", []) if isinstance(raw_json, dict) else None

    job, should_queue = create_bulk_job(db, body, raw_recipients_payload=raw_recipients)

    if should_queue:
        if process_async:
            background_tasks.add_task(process_job_background, job.id)
        else:
            # Synchronous processing mode
            process_job_background(job.id, db=db)
            db.refresh(job)

    return build_job_status_response(job)

@router.get("", response_model=List[JobStatusResponse])
def list_certificate_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all certificate generation jobs with pagination."""
    jobs = db.query(CertificateJob).order_by(CertificateJob.created_at.desc()).offset(skip).limit(limit).all()
    return [build_job_status_response(job) for job in jobs]

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check the status and progress of a certificate generation job."""
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")
    return build_job_status_response(job)

@router.get("/{job_id}/details", response_model=JobSummaryResponse)
def get_job_details(job_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed progress of a job including successful and failed recipient certificates."""
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")
    
    successful = [build_cert_response(c) for c in job.certificates if c.status == CertificateStatus.GENERATED]
    failed = [build_cert_response(c) for c in job.certificates if c.status == CertificateStatus.FAILED]

    return JobSummaryResponse(
        job=build_job_status_response(job),
        successful_certificates=successful,
        failed_certificates=failed
    )

@router.get("/{job_id}/download-zip")
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """Download a ZIP file archive containing all successfully generated certificates for a job."""
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")
    
    successful_certs = [c for c in job.certificates if c.status == CertificateStatus.GENERATED]
    if not successful_certs:
        raise HTTPException(status_code=400, detail="No generated certificates available for download in this job.")

    zip_path = create_job_zip_archive(job)
    return FileResponse(
        path=str(zip_path),
        filename=f"certificates_job_{job.id}.zip",
        media_type="application/zip"
    )
