"""Application settings loaded from environment variables."""

from pydantic import ConfigDict, Field, model_validator
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
    # One bot endpoint serves several GitHub webhooks (org- or repo-level), each
    # with its own secret. A delivery is accepted if it matches ANY configured
    # secret. `github_webhook_secret` is the legacy single value;
    # `github_webhook_secrets` is a comma-separated list of additional secrets.
    github_webhook_secret: str | None = Field(
        None, description="Primary GitHub webhook secret for HMAC verification"
    )
    github_webhook_secrets: str | None = Field(
        None, description="Additional comma-separated webhook secrets (one per repo/org)"
    )

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

    @property
    def webhook_secrets(self) -> list[str]:
        """All configured webhook secrets, de-duplicated and order-preserving."""
        raw: list[str] = []
        if self.github_webhook_secret:
            raw.append(self.github_webhook_secret)
        if self.github_webhook_secrets:
            raw.extend(self.github_webhook_secrets.split(","))

        seen: set[str] = set()
        result: list[str] = []
        for secret in (s.strip() for s in raw):
            if secret and secret not in seen:
                seen.add(secret)
                result.append(secret)
        return result

    @model_validator(mode="after")
    def _require_at_least_one_secret(self) -> "Settings":
        if not self.webhook_secrets:
            raise ValueError(
                "No webhook secret configured: set GITHUB_WEBHOOK_SECRET "
                "and/or GITHUB_WEBHOOK_SECRETS"
            )
        return self


settings = Settings()
