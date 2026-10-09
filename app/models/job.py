import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"

class CertificateJob(Base):
    __tablename__ = "certificate_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    course_or_event = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    template_id = Column(String(50), default="classic_gold", nullable=False)
    send_email = Column(Boolean, default=False, nullable=False)
    
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    total_recipients = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    successful_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    certificates = relationship("CertificateRecord", back_populates="job", cascade="all, delete-orphan")
