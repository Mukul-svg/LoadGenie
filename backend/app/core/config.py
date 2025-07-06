"""
Application configuration settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # App configuration
    APP_NAME: str = "LoadGenie API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered k6 load testing script generator"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # AI Service configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.8"))
    AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "60"))
    
    # K6 Runner configuration
    K6_RESULTS_DIR: str = os.getenv("K6_RESULTS_DIR", "/tmp/k6_results")
    K6_TIMEOUT: int = int(os.getenv("K6_TIMEOUT", "300"))  # 5 minutes default
    
    # Database configuration (for future SQLite integration)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./loadgenie.db")
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG
    
    def validate(self) -> None:
        """Validate required configuration"""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")

# Global settings instance
settings = Settings()
