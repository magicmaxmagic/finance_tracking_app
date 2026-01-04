"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finance_user:finance_password@postgres:5432/finance_db"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    REFRESH_SECRET_KEY: str = "dev-refresh-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

    # Cookies
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Optional[str] = None

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security headers / hosts
    SECURITY_HEADERS_ENABLED: bool = True
    ENFORCE_HTTPS: bool = False
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    HSTS_MAX_AGE: int = 31536000
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = False
    CONTENT_SECURITY_POLICY: Optional[str] = None

    # Upload limits
    MAX_ICS_UPLOAD_BYTES: int = 5_000_000

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    REDIS_URL: Optional[str] = None

    # Token blacklist
    ENABLE_TOKEN_BLACKLIST: bool = True
    TOKEN_BLACKLIST_PREFIX: str = "token:blacklist:"

    # Audit logging
    AUDIT_LOG_ENABLED: bool = True

    # Auth flows
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24

    # Metrics
    PROMETHEUS_METRICS_ENABLED: bool = True

    # Stripe billing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_PRO_MONTHLY: Optional[str] = None
    STRIPE_PRICE_ID_PRO_ANNUAL: Optional[str] = None
    STRIPE_SUCCESS_URL: str = "http://localhost:3000/pricing?checkout=success"
    STRIPE_CANCEL_URL: str = "http://localhost:3000/pricing?checkout=cancel"
    STRIPE_PORTAL_RETURN_URL: str = "http://localhost:3000/settings"

    # Google Calendar OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
