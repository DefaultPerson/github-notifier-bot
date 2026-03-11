"""Multi-channel routing logic (repo -> channels)."""

import fnmatch

from bot.models.config import ChannelConfig, Config


class ChannelRouter:
    """Routes events to matching channels based on repo and event type."""

    def __init__(self, config: Config):
        self._channels = config.channels

    def find_channels(self, repo: str, event_type: str) -> list[ChannelConfig]:
        """
        Find all channels that should receive this event.

        Args:
            repo: Repository full name (e.g., "org/repo")
            event_type: Internal event type (e.g., "push", "security")

        Returns:
            List of matching channel configurations
        """
        matches = []
        for channel in self._channels:
            if not self._repo_matches(repo, channel.repos):
                continue
            if channel.events and event_type not in channel.events:
                continue
            matches.append(channel)
        return matches

    def _repo_matches(self, repo: str, patterns: list[str]) -> bool:
        """Check if repo matches any of the patterns."""
        for pattern in patterns:
            # Handle org/* wildcard
            if pattern.endswith("/*"):
                org = pattern[:-2]
                if repo.startswith(f"{org}/"):
                    return True
            # Handle exact match or fnmatch patterns
            elif fnmatch.fnmatch(repo, pattern):
                return True
        return False
