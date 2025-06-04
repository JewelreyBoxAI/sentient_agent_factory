"""
Application settings and configuration
"""
import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Database (Optional for SQLite prototype)
    DATABASE_URL: Optional[str] = Field(default=None)
    DIRECT_DATABASE_URL: Optional[str] = Field(default=None)
    
    # OpenAI (Required)
    OPENAI_API_KEY: str = Field(default="sk-test-placeholder")
    
    # Authentication (Optional for prototype)
    CLERK_SECRET_KEY: str = Field(default="")
    CLERK_PUBLISHABLE_KEY: str = Field(default="")
    JWT_SECRET: str = Field(default="dev_jwt_secret")
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = Field(default="ddbjhqnuk")
    CLOUDINARY_API_KEY: str = Field(default="711243612821432")
    CLOUDINARY_API_SECRET: str = Field(default="")
    
    # Redis (Optional)
    REDIS_URL: str = Field(default="redis://localhost:6379")
    
    # Stripe (Optional)
    STRIPE_API_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    
    # API Configuration
    API_HOST: str = Field(default="127.0.0.1")
    API_PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)  # Default to True for prototype
    
    # CORS - Handle both string and list
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(default="http://localhost:3000")
    
    # Memory & Vector Store
    FAISS_INDEX_PATH: str = Field(default="./data/faiss_index")
    MAX_TOKENS_LIMIT: int = Field(default=4000)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=3600)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list"""
        if isinstance(v, str):
            # Handle comma-separated string
            if ',' in v:
                return [origin.strip() for origin in v.split(',')]
            else:
                return [v.strip()]
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 