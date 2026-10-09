import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class CertificateStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"

class CertificateRecord(Base):
    __tablename__ = "certificate_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("certificate_jobs.id"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_identifier = Column(String(100), nullable=True)
    custom_attributes = Column(JSON, nullable=True)
    
    status = Column(SQLEnum(CertificateStatus), default=CertificateStatus.PENDING, nullable=False)
    certificate_code = Column(String(100), unique=True, nullable=True, index=True)
    
    file_path = Column(String(500), nullable=True)
    preview_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    
    email_sent = Column(Boolean, default=False, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("CertificateJob", back_populates="certificates")
