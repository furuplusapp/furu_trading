from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    app_name: str = "Furu AI"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str
    test_database_url: str
    
    # Redis
    redis_url: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Email
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    from_email: str
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()