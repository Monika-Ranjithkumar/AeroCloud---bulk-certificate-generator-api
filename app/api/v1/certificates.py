from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.certificate import CertificateRecord, CertificateStatus
from app.models.job import CertificateJob
from app.schemas.certificate import CertificateResponse, VerificationResponse

router = APIRouter()

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
        generated_at=cert.generated_at,
        created_at=cert.created_at
    )

@router.get("/verify/{certificate_code}", response_model=VerificationResponse)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    """Verify authenticity of a certificate using its unique certificate code."""
    cert = db.query(CertificateRecord).filter(
        CertificateRecord.certificate_code == certificate_code
    ).first()

    if not cert or cert.status != CertificateStatus.GENERATED:
        return VerificationResponse(
            valid=False,
            message="Invalid or non-existent certificate code."
        )

    job = db.query(CertificateJob).filter(CertificateJob.id == cert.job_id).first()

    return VerificationResponse(
        valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        course_or_event=job.course_or_event if job else "N/A",
        issuer_name=job.issuer_name if job else "N/A",
        issue_date=job.issue_date if job else "N/A",
        generated_at=cert.generated_at,
        message="Certificate is authentic and valid."
    )

@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate_metadata(certificate_id: str, db: Session = Depends(get_db)):
    """Get certificate metadata by Certificate Record ID."""
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{certificate_id}' not found.")
    return build_cert_response(cert)

@router.get("/{certificate_id}/download")
def download_certificate_pdf(certificate_id: str, db: Session = Depends(get_db)):
    """Download the PDF certificate file."""
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{certificate_id}' not found.")
    
    if cert.status != CertificateStatus.GENERATED or not cert.file_path or not Path(cert.file_path).exists():
        raise HTTPException(
            status_code=400,
            detail=f"Certificate PDF is not available. Status: {cert.status}. Error: {cert.error_message or 'File missing'}"
        )

    clean_filename = f"{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"
    return FileResponse(
        path=cert.file_path,
        filename=clean_filename,
        media_type="application/pdf"
    )

@router.get("/{certificate_id}/preview")
def preview_certificate_png(certificate_id: str, db: Session = Depends(get_db)):
    """View / Download PNG image preview of certificate."""
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{certificate_id}' not found.")
    
    if cert.status != CertificateStatus.GENERATED or not cert.preview_path or not Path(cert.preview_path).exists():
        raise HTTPException(
            status_code=400,
            detail=f"Certificate preview image is not available. Status: {cert.status}."
        )

    return FileResponse(
        path=cert.preview_path,
        media_type="image/png"
    )
