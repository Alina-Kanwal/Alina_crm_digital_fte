"""
Application configuration management using pydantic-settings.

Provides type-safe configuration from environment variables
with validation and defaults.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have defaults and type validation.
    """

    # Application
    APP_NAME: str = Field(default="Digital FTE Agent", env="APP_NAME")
    APP_ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")

    # Database (PostgreSQL with pgvector)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://dte_user:dte_password@localhost:5432/dte_db",
        env="DATABASE_URL",
    )
    POOL_SIZE: int = Field(default=20, env="POOL_SIZE")
    MAX_OVERFLOW: int = Field(default=10, env="MAX_OVERFLOW")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    OPENAI_TIMEOUT: int = Field(default=30, env="OPENAI_TIMEOUT")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_CONSUMER_GROUP: str = Field(
        default="digital-fte-consumers", env="KAFKA_CONSUMER_GROUP"
    )
    KAFKA_MAX_POLL_RECORDS: int = Field(default=100, env="KAFKA_MAX_POLL_RECORDS")
    KAFKA_SESSION_TIMEOUT_MS: int = Field(default=30000, env="KAFKA_SESSION_TIMEOUT_MS")

    # Redis (optional)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=True, env="REDIS_ENABLED")

    # Gmail API
    GMAIL_CREDENTIALS_PATH: str = Field(
        default="credentials/gmail.json", env="GMAIL_CREDENTIALS_PATH"
    )
    GMAIL_POLL_INTERVAL_MINUTES: int = Field(default=5, env="GMAIL_POLL_INTERVAL_MINUTES")

    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = Field(default=None, env="TWILIO_WHATSAPP_NUMBER")
    TWILIO_WEBHOOK_URL: str = Field(
        default="/api/v1/channels/whatsapp/webhook",
        env="TWILIO_WEBHOOK_URL",
    )

    # Agent Configuration
    AGENT_ESCALATION_THRESHOLD: int = Field(default=3, env="AGENT_ESCALATION_THRESHOLD")
    AGENT_SENTIMENT_THRESHOLD: float = Field(default=0.7, env="AGENT_SENTIMENT_THRESHOLD")
    AGENT_RESPONSE_TIMEOUT: int = Field(default=30, env="AGENT_RESPONSE_TIMEOUT")
    AGENT_MAX_HISTORY_ITEMS: int = Field(default=10, env="AGENT_MAX_HISTORY_ITEMS")

    # Cross-Channel Identification
    CROSS_CHANNEL_ID_THRESHOLD: float = Field(
        default=0.95, env="CROSS_CHANNEL_ID_THRESHOLD"
    )
    ENABLE_CROSS_CHANNEL_MATCHING: bool = Field(
        default=True, env="ENABLE_CROSS_CHANNEL_MATCHING"
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

    # Caching
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # seconds

    # Observability
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    TRACING_ENABLED: bool = Field(default=True, env="TRACING_ENABLED")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # CORS
    ALLOW_ORIGINS: List[str] = Field(
        default=["*"], env="ALLOW_ORIGINS"
    )

    @validator("APP_ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment value."""
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be 'development', 'staging', or 'production'")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level value."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("CROSS_CHANNEL_ID_THRESHOLD")
    def validate_id_threshold(cls, v):
        """Validate cross-channel ID threshold."""
        if not 0.5 <= v <= 1.0:
            raise ValueError("CROSS_CHANNEL_ID_THRESHOLD must be between 0.5 and 1.0")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.APP_ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.APP_ENVIRONMENT.lower() == "development"

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create singleton settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience functions for accessing common settings
def get_database_url() -> str:
    """Get database URL."""
    return get_settings().DATABASE_URL


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return get_settings().OPENAI_API_KEY


def get_kafka_bootstrap_servers() -> str:
    """Get Kafka bootstrap servers."""
    return get_settings().KAFKA_BOOTSTRAP_SERVERS


def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().is_development


def is_production() -> bool:
    """Check if running in production mode."""
    return get_settings().is_production
