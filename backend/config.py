"""
============================================
FASTAPI BACKEND - CONFIGURATION
============================================
Purpose: Environment configuration and settings
Version: 1.0
Created: 2025-11-20
============================================
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Rate Limiting (optional)
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
