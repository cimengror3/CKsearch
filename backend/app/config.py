"""
CKSEARCH API - Configuration
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/cksearch")
    
    # Security
    admin_secret: str = os.getenv("ADMIN_SECRET", "cksearch-admin-secret-change-me")
    jwt_secret: str = os.getenv("JWT_SECRET", "cksearch-jwt-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # App
    app_name: str = "CKSEARCH API"
    current_version: str = os.getenv("CURRENT_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Limits
    free_daily_limit: int = 5
    free_username_unlimited: bool = True
    
    # Contact
    contact_telegram: str = "@cimenk"
    contact_info: str = "Chat @cimenk untuk upgrade premium"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
