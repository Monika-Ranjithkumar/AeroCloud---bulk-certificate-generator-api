import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    BASE_DIR: Path = BASE_DIR
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/certificates.db"
    
    # Certificate Storage
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = BASE_DIR / "storage" / "certificates"
    PREVIEWS_DIR: Path = BASE_DIR / "storage" / "previews"
    EXPORTS_DIR: Path = BASE_DIR / "storage" / "exports"
    
    # Certificate Generator Settings
    DEFAULT_ISSUER: str = "AeroCloud Certification Authority"
    BASE_VERIFICATION_URL: str = "http://localhost:8000/api/v1/certificates/verify"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
settings.PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
