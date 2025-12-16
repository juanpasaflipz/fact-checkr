import os
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Centralized configuration for the application.
    Loads values from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

    # --- General ---
    PROJECT_NAME: str = "FactCheckr MX"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # --- API & Security ---
    # CORS_ORIGINS can be a comma-separated string or a list of strings
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://factcheck.mx",
        "https://www.factcheck.mx",
        "https://app.factcheck.mx",
        "https://www.app.factcheck.mx",
        "https://fact-checkr-production.up.railway.app",
        "https://fact-checkr.vercel.app",
        "https://fact-checkr-juanpasa.vercel.app",
    ]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    FRONTEND_URL: str = "http://localhost:3000"

    # --- Database ---
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # --- Authentication (Firebase) ---
    FIREBASE_CREDENTIALS_B64: Optional[str] = None
    
    # --- Monitoring ---
    SENTRY_DSN: Optional[str] = None

    # --- External APIs ---
    # Telegraph
    TELEGRAPH_ACCESS_TOKEN: Optional[str] = None
    
    # Twitter/X
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    # AI Providers
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # --- Search & Scraping ---
    SERPER_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Facebook / Instagram
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_USER_ID: Optional[str] = None

    # --- Redis & Infrastructure ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PUBLIC_URL: Optional[str] = None
    RAILWAY_PRIVATE_DOMAIN: Optional[str] = None
    RAILWAY_TCP_PROXY_DOMAIN: Optional[str] = None

    # --- Feature Flags & Limits ---
    AUTO_PUBLISH_BLOG: bool = False
    AUTO_POST_TO_TWITTER: bool = False
    USE_MULTI_AGENT_VERIFICATION: bool = False
    BLOG_FREE_TIER_LIMIT: int = 3
    SCRAPING_KEYWORD_PRIORITY: str = "default"
    MARKET_INTELLIGENCE_MODEL: str = "haiku"

    # --- Stripe Payment ---
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRO_MONTHLY_PRICE_ID: Optional[str] = None
    STRIPE_PRO_YEARLY_PRICE_ID: Optional[str] = None
    STRIPE_TEAM_MONTHLY_PRICE_ID: Optional[str] = None
    STRIPE_TEAM_YEARLY_PRICE_ID: Optional[str] = None

    # --- Cloud Tasks ---
    CLOUD_TASKS_EMULATE_SYNC: str = "false"
    GCP_PROJECT_ID: Optional[str] = None
    GCP_LOCATION: str = "us-central1"
    CLOUD_TASKS_QUEUE: str = "default"
    TASKS_TARGET_BASE_URL: Optional[str] = None
    TASKS_OIDC_SERVICE_ACCOUNT_EMAIL: Optional[str] = None
    TASK_SECRET: Optional[str] = None

    # --- WhatsApp ---
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "my_secret"
    WHATSAPP_APP_SECRET: Optional[str] = None

    # --- Google Auth ---
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    def get_frontend_url(self) -> str:
        """Helper to get clean frontend URL"""
        url = self.FRONTEND_URL
        if "wwww" in url:
            url = url.replace("wwww", "www")
        return url.rstrip("/")

# Global settings instance
settings = Settings()
