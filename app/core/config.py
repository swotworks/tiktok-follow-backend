import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TikTok Follow SaaS"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "supersecretkey_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/follow_exchanger")
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
