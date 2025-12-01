"""
Configuration Management for ELCS Backend
Loads environment variables and provides centralized config access
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "INDAS Exhibition Lead Capture System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # MSSQL Database
    MSSQL_CONN_STRING: str
    DB_POOL_SIZE: int = 5
    DB_TIMEOUT: int = 30

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000

    # WhatsApp Gateway (Third-Party API)
    WHATSAPP_API_URL: str = "http://103.150.136.76:8090"
    WHATSAPP_API_KEY: str  # X-API-Key header (your user API key)
    WHATSAPP_ACCOUNT_TOKEN: str  # Authorization: Bearer token (WhatsApp account token)
    WHATSAPP_PHONE_NUMBER: str  # Your WhatsApp business phone number
    EXHIBITION_ADMIN_PHONE: str = "916263235861"  # Default admin phone for notifications

    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: list = [".jpg", ".jpeg", ".png"]
    ALLOWED_AUDIO_EXTENSIONS: list = [".webm", ".ogg", ".mp3", ".wav"]

    # OCR Settings
    TESSERACT_CMD: Optional[str] = None  # Path to tesseract executable
    OCR_LANGUAGE: str = "eng+hin"  # English + Hindi

    # API Settings
    API_PREFIX: str = "/api"
    API_BASE_URL: str = "http://localhost:9000"  # Backend API URL (for internal calls)
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://103.150.136.76:3003"  # Production frontend
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience access
settings = get_settings()


# Create upload directories if they don't exist
def init_storage():
    """Initialize storage directories"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "cards"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "audio"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "documents"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "whatsapp"), exist_ok=True)
    print(f"✅ Storage directories initialized at: {settings.UPLOAD_DIR}")
