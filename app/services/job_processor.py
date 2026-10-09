import logging
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import SessionLocal, init_db
from app.models.job import CertificateJob, JobStatus
from app.models.certificate import CertificateRecord, CertificateStatus
from app.schemas.job import JobCreateRequest
from app.schemas.recipient import RecipientInput
from app.services.generator import CertificateGenerator, generate_certificate_code
from app.services.email_service import EmailService
from app.config import settings

logger = logging.getLogger("bulk_certificate_processor")

def process_job_background(job_id: str, db: Optional[Session] = None):
    """
    Background worker task to process certificate generation for a batch job.
    Uses provided DB session or creates a new one.
    """
    should_close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close_db = True

    try:
        job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for background processing.")
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        # Query pending records
        pending_records = db.query(CertificateRecord).filter(
            CertificateRecord.job_id == job_id,
            CertificateRecord.status == CertificateStatus.PENDING
        ).all()

        for record in pending_records:
            try:
                # Generate unique code if not assigned
                if not record.certificate_code:
                    record.certificate_code = generate_certificate_code()

                # Generate PDF certificate with selected template
                pdf_path = CertificateGenerator.generate_pdf(
                    certificate_code=record.certificate_code,
                    recipient_name=record.recipient_name,
                    course_or_event=job.course_or_event,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    custom_attributes=record.custom_attributes,
                    template_id=job.template_id
                )

                # Generate PNG preview with selected template
                preview_path = CertificateGenerator.generate_preview(
                    certificate_code=record.certificate_code,
                    recipient_name=record.recipient_name,
                    course_or_event=job.course_or_event,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    template_id=job.template_id
                )

                record.status = CertificateStatus.GENERATED
                record.file_path = str(pdf_path)
                record.preview_path = str(preview_path)
                record.generated_at = datetime.utcnow()
                record.error_message = None

                # Email delivery directly to recipient
                if job.send_email:
                    email_ok = EmailService.send_certificate_email(
                        recipient_email=record.recipient_email,
                        recipient_name=record.recipient_name,
                        course_or_event=job.course_or_event,
                        issuer_name=job.issuer_name,
                        certificate_code=record.certificate_code,
                        pdf_path=pdf_path
                    )
                    if email_ok:
                        record.email_sent = True
                        record.email_sent_at = datetime.utcnow()

                job.successful_count += 1

            except Exception as e:
                logger.exception(f"Failed to generate certificate for record {record.id}: {str(e)}")
                record.status = CertificateStatus.FAILED
                record.error_message = f"Generation error: {str(e)}"
                job.failed_count += 1

            finally:
                job.processed_count += 1
                job.updated_at = datetime.utcnow()
                db.commit()

        # Update final job status
        if job.failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif job.successful_count > 0:
            job.status = JobStatus.PARTIALLY_COMPLETED
        else:
            job.status = JobStatus.FAILED
            job.error_summary = "All certificate generations failed in this batch."

        job.updated_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        logger.exception(f"Critical unhandled error in job processor {job_id}: {str(exc)}")
        if 'job' in locals() and job:
            job.status = JobStatus.FAILED
            job.error_summary = f"System error: {str(exc)}"
            db.commit()
    finally:
        if should_close_db and db:
            db.close()

def create_bulk_job(db: Session, request_data: JobCreateRequest, raw_recipients_payload: List[Dict[str, Any]] = None) -> Tuple[CertificateJob, bool]:
    """
    Creates a new bulk certificate job, pre-validating recipient items.
    Returns (job_instance, should_queue_background_task).
    """
    issuer_name = request_data.issuer_name or settings.DEFAULT_ISSUER
    template_id = request_data.template_id or "classic_gold"
    send_email = request_data.send_email or False
    
    # Instantiate CertificateJob
    job = CertificateJob(
        title=request_data.title,
        issuer_name=issuer_name,
        course_or_event=request_data.course_or_event,
        issue_date=request_data.issue_date,
        template_id=template_id,
        send_email=send_email,
        status=JobStatus.PENDING,
        total_recipients=0,
        processed_count=0,
        successful_count=0,
        failed_count=0
    )
    db.add(job)
    db.flush()  # Obtain job.id

    recipients_to_process = []
    
    items_to_eval = raw_recipients_payload if raw_recipients_payload is not None else [r.model_dump() for r in request_data.recipients]
    job.total_recipients = len(items_to_eval)

    for item in items_to_eval:
        try:
            validated_recipient = RecipientInput(**item)
            
            record = CertificateRecord(
                job_id=job.id,
                recipient_name=validated_recipient.name,
                recipient_email=validated_recipient.email,
                recipient_identifier=validated_recipient.identifier,
                custom_attributes=validated_recipient.custom_attributes,
                status=CertificateStatus.PENDING,
                certificate_code=generate_certificate_code()
            )
            recipients_to_process.append(record)

        except ValidationError as val_err:
            error_details = "; ".join([f"{e['loc'][-1] if e['loc'] else 'field'}: {e['msg']}" for e in val_err.errors()])
            failed_record = CertificateRecord(
                job_id=job.id,
                recipient_name=item.get("name") or "Unknown",
                recipient_email=item.get("email") or "invalid@email.com",
                recipient_identifier=item.get("identifier"),
                custom_attributes=item.get("custom_attributes"),
                status=CertificateStatus.FAILED,
                error_message=f"Validation failed: {error_details}"
            )
            db.add(failed_record)
            job.processed_count += 1
            job.failed_count += 1

    if recipients_to_process:
        db.add_all(recipients_to_process)

    if job.failed_count == job.total_recipients:
        job.status = JobStatus.FAILED
        job.error_summary = "All provided recipients failed initial data validation."
        should_queue = False
    else:
        should_queue = True

    db.commit()
    db.refresh(job)
    return job, should_queue

def create_job_zip_archive(job: CertificateJob) -> Path:
    """Creates a ZIP file containing all successfully generated PDF certificates for a job."""
    zip_filename = f"job_{job.id}_certificates.zip"
    zip_path = settings.EXPORTS_DIR / zip_filename

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for cert in job.certificates:
            if cert.status == CertificateStatus.GENERATED and cert.file_path and Path(cert.file_path).exists():
                arcname = f"{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"
                zipf.write(cert.file_path, arcname=arcname)

    return zip_path
