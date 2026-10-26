"""Production-ready application configuration management using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized typed application settings loaded from environment variables and .env file."""

    app_name: str = Field(default="Scientific Experiments Registry", description="Application display name")
    environment: str = Field(
        default="development", description="Runtime environment: development, test, production"
    )
    host: str = Field(default="0.0.0.0", description="Bind host address")
    port: int = Field(default=8000, description="Bind port number")

    database_url: str = Field(
        default="sqlite:///./data/experiments.db",
        description="SQLAlchemy database connection URL",
    )
    log_level: str = Field(default="INFO", description="Standard logging level (DEBUG, INFO, WARNING, ERROR)")

    secret_key: str = Field(
        default="dev-secret-key-must-be-overridden-in-production",
        description="Application secret key for security signatures",
    )
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origin domains")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment.lower() == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton instance."""
    return Settings()
