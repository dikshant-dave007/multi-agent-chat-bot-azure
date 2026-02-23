"""
Configuration management for the multi-agent automation engine.

This module handles loading and validation of all configuration
settings from environment variables and configuration files.
"""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI configuration."""

    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    api_key: Optional[str] = Field(None, description="API key (optional with managed identity)")
    deployment_name: str = Field(..., description="Deployment name for the model")
    api_version: str = Field(default="2024-02-15-preview", description="API version")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=60, description="Request timeout in seconds")

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class CosmosDBSettings(BaseSettings):
    """Azure Cosmos DB configuration."""

    endpoint: str = Field(..., description="Cosmos DB endpoint URL")
    key: Optional[str] = Field(None, description="Cosmos DB key (optional with managed identity)")
    database_name: str = Field(default="multi-agent-engine", description="Database name")
    container_name: str = Field(default="tasks", description="Container name")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(
        env_prefix="COSMOS_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class KeyVaultSettings(BaseSettings):
    """Azure Key Vault configuration."""

    url: Optional[str] = Field(default=None, description="Key Vault URL (optional)")
    use_managed_identity: bool = Field(default=False, description="Use managed identity for auth")

    model_config = SettingsConfigDict(
        env_prefix="KEY_VAULT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class APISettings(BaseSettings):
    """FastAPI configuration."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=4, description="Number of worker processes")
    timeout_seconds: int = Field(default=300, description="Request timeout")
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    enable_auth: bool = Field(default=True, description="Enable authentication")

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")
    enable_file_logging: bool = Field(default=False, description="Enable file logging")
    log_file_path: str = Field(default="logs/app.log", description="Log file path")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class PerformanceSettings(BaseSettings):
    """Performance and scaling configuration."""

    max_concurrent_tasks: int = Field(default=10, description="Max concurrent task executions")
    task_timeout_seconds: int = Field(default=600, description="Default task timeout")
    retry_max_attempts: int = Field(default=3, description="Max retry attempts")
    retry_backoff_seconds: int = Field(default=2, description="Retry backoff base time")
    retry_backoff_max_seconds: int = Field(default=60, description="Max retry backoff time")
    enable_response_caching: bool = Field(default=True, description="Enable LLM response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    model_config = SettingsConfigDict(
        env_prefix="PERF_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""

    enable_application_insights: bool = Field(default=False, description="Enable Application Insights")
    application_insights_connection_string: Optional[str] = Field(
        None, description="Application Insights connection string"
    )
    enable_prometheus: bool = Field(default=False, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics endpoint port")

    model_config = SettingsConfigDict(
        env_prefix="MONITORING_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")

    # Azure settings - FIXED: Initialize lazily, not with default_factory
    azure_openai: Optional[AzureOpenAISettings] = None
    cosmos_db: Optional[CosmosDBSettings] = None
    key_vault: Optional[KeyVaultSettings] = None

    # Application settings
    api: Optional[APISettings] = None
    logging: Optional[LoggingSettings] = None
    performance: Optional[PerformanceSettings] = None
    monitoring: Optional[MonitoringSettings] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings and nested configurations."""
        super().__init__(**kwargs)
        
        # Manually initialize nested settings after parent loads .env
        if self.azure_openai is None:
            self.azure_openai = AzureOpenAISettings()
        if self.cosmos_db is None:
            self.cosmos_db = CosmosDBSettings()
        if self.key_vault is None:
            self.key_vault = KeyVaultSettings()
        if self.api is None:
            self.api = APISettings()
        if self.logging is None:
            self.logging = LoggingSettings()
        if self.performance is None:
            self.performance = PerformanceSettings()
        if self.monitoring is None:
            self.monitoring = MonitoringSettings()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v.lower()

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        Settings: Reloaded application settings
    """
    global _settings
    _settings = Settings()
    return _settings
