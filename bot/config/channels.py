"""Config loader for channel routing."""

from pathlib import Path

import yaml

from bot.models.config import Config


def _split_csv(raw: str | None) -> list[str] | None:
    """Split a comma-separated env value into stripped items; None/blank -> None."""
    if raw is None:
        return None
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or None


def load_config_from_env(
    chat_id: int,
    thread_id: int | None,
    repos: str,
    events: str | None = None,
    exclude_events: str | None = None,
) -> Config:
    """Load a single-channel config from environment variables.

    Args:
        chat_id: Telegram chat ID
        thread_id: Telegram thread ID (optional)
        repos: Comma-separated repo patterns (``*`` matches every repository)
        events: Comma-separated event allowlist (optional, None = all events)
        exclude_events: Comma-separated event blacklist (optional)
    """
    data = {
        "channels": [
            {
                "chat_id": chat_id,
                "thread_id": thread_id,
                "repos": _split_csv(repos) or [],
                "events": _split_csv(events),
                "exclude_events": _split_csv(exclude_events),
            }
        ]
    }
    return Config.model_validate(data)


def load_config_from_file(path: str | Path) -> Config:
    """Load config from YAML file.

    Raises:
        FileNotFoundError: the file does not exist.
        ValueError: the file declares no channels — a deployment that forgot
            both ``CHANNEL_*`` and a real file must fail loudly, not route
            every event to nowhere.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    config = Config.model_validate(data)
    if not config.channels:
        raise ValueError(
            f"No channels configured in {path}: set CHANNEL_CHAT_ID/CHANNEL_REPOS "
            "or add at least one channel to the file"
        )
    return config
