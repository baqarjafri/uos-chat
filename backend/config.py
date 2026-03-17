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
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    
    # CORS - Will be updated based on environment
    CORS_ORIGINS: str = "https://ai-uos.up.railway.app,http://localhost:3000,http://localhost:5173"
    
    @property
    def ALLOWED_ORIGINS(self) -> list:
        """Get CORS origins with production origin always included"""
        origins = self.CORS_ORIGINS.split(",")
        # Always ensure production frontend is included
        production_origin = "https://ai-uos.up.railway.app"
        if production_origin not in origins:
            origins.append(production_origin)
        return origins
    
    # Environment detection
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", os.environ.get("API_PORT", "8001")))  # Railway sets PORT, local uses API_PORT
    DEBUG: bool = False
    
    # Railway specific settings
    RAILWAY_ENVIRONMENT: str = ""
    RAILWAY_SERVICE_NAME: str = ""
    
    # Rate Limiting (optional)
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
