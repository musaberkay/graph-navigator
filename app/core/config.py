"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Application
    APP_NAME: str = "graph-navigator"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = "mysql+asyncmy://graphuser:graphpassword@localhost:3306/graphdb"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # API
    API_V1_PREFIX: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


settings = get_settings()
