"""
Configuration management for the Digital FTE agent.
Loads environment variables and provides typed settings.
"""
from pydantic import BaseSettings, Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Digital FTE Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(False, env="DEBUG")

    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")

    # Database
    POSTGRES_USER: str = Field("dte_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("dte_password", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("dte_db", env="POSTGRES_DB")
    POSTGRES_HOST: str = Field("localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AI/OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-4o", env="OPENAI_MODEL")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC_INQUIRIES: str = Field("customer_inquiries", env="KAFKA_TOPIC_INQUIRIES")
    KAFKA_TOPIC_RESPONSES: str = Field("agent_responses", env="KAFKA_TOPIC_RESPONSES")

    # Security
    JWT_SECRET_KEY: str = Field("your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(24, env="JWT_EXPIRATION_HOURS")

    # External Services
    GMAIL_CLIENT_ID: Optional[str] = Field(None, env="GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: Optional[str] = Field(None, env="GMAIL_CLIENT_SECRET")
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = Field(None, env="TWILIO_WHATSAPP_NUMBER")

    # Monitoring
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # Cost Control
    MAX_DAILY_COST_USD: float = Field(2.74, env="MAX_DAILY_COST_USD")  # ~$1000/year

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
settings = Settings()