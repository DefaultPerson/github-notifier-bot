"""Pydantic models for config.yaml schema."""

from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "push",
    "release",
    "pull_request",
    "review",
    "review_comment",
    "deploy_key",
    "security",
]


class ChannelConfig(BaseModel):
    """Configuration for a single Telegram channel."""

    chat_id: int = Field(..., description="Telegram chat ID")
    thread_id: int | None = Field(None, description="Telegram thread/topic ID (optional)")
    repos: list[str] = Field(..., description="List of repos: 'org/repo' or 'org/*' for wildcard")
    events: list[EventType] | None = Field(
        None, description="Event types to receive (None = all events)"
    )
    exclude_events: list[EventType] | None = Field(
        None, description="Event types to skip (applied after `events` allowlist)"
    )


class Config(BaseModel):
    """Root configuration model."""

    channels: list[ChannelConfig] = Field(..., description="List of channel configurations")
