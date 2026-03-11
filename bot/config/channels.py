"""Config loader for channel routing."""

from pathlib import Path

import yaml

from bot.models.config import Config


def load_config_from_env(chat_id: int, thread_id: int | None, repos: str) -> Config:
    """Load config from environment variables.

    Args:
        chat_id: Telegram chat ID
        thread_id: Telegram thread ID (optional)
        repos: Comma-separated repo patterns
    """
    repo_list = [r.strip() for r in repos.split(",") if r.strip()]
    data = {
        "channels": [
            {
                "chat_id": chat_id,
                "thread_id": thread_id,
                "repos": repo_list,
                "events": None,
            }
        ]
    }
    return Config.model_validate(data)


def load_config_from_file(path: str | Path) -> Config:
    """Load config from YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)
