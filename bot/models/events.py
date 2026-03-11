"""Pydantic models for GitHub webhook events."""

from dataclasses import dataclass


@dataclass
class VulnerabilityItem:
    """Single vulnerability alert item."""

    package_name: str
    version: str
    severity: str
    summary: str

    @property
    def unique_key(self) -> str:
        """Unique key for deduplication within a batch."""
        return f"{self.package_name}|{self.version}|{self.severity}"


@dataclass
class RepoBatch:
    """Batch of vulnerabilities for a single repository."""

    repo_name: str
    repo_url: str
    items: dict[str, VulnerabilityItem]  # unique_key -> item
    first_at: float = 0
    last_at: float = 0
