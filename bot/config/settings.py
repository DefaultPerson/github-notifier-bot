"""Application settings loaded from environment variables."""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str = Field(..., description="Telegram Bot API token")

    # GitHub Webhook
    github_webhook_secret: str = Field(..., description="GitHub webhook secret for HMAC verification")

    # Server
    host: str = Field("0.0.0.0", description="Webhook server host")
    port: int = Field(8000, description="Webhook server port")

    # Config (file or env)
    config_path: str = Field("config.yaml", description="Path to channels config")
    channel_chat_id: int | None = Field(None, description="Telegram chat ID")
    channel_thread_id: int | None = Field(None, description="Telegram thread ID")
    channel_repos: str | None = Field(None, description="Comma-separated repo patterns")

    # Dedup & Batching
    dedup_ttl_seconds: int = Field(10, description="Dedup TTL in seconds")
    security_batch_window_seconds: int = Field(60, description="Security alert batch window")

    # Logging
    log_level: str = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")


settings = Settings()
