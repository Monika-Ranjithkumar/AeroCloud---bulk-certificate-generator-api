from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of recipient")
    email: EmailStr = Field(..., description="Recipient email address")
    identifier: Optional[str] = Field(None, max_length=100, description="Optional unique identifier like Student ID")
    custom_attributes: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary custom recipient attributes (e.g. grade, role)")

    @field_validator("name")
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Recipient name cannot be blank or whitespace-only")
        return v.strip()

class RawRecipientInput(BaseModel):
    """Schema for validating unstructured or partially invalid recipient inputs during batch import."""
    name: Optional[str] = None
    email: Optional[str] = None
    identifier: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
