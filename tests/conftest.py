"""Pytest fixtures for github-notifier-bot tests."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def sample_push_payload() -> dict:
    """Sample GitHub push event payload."""
    return {
        "ref": "refs/heads/main",
        "after": "abc123def456789",
        "repository": {
            "full_name": "hydra-monitors/hm-core",
            "html_url": "https://github.com/hydra-monitors/hm-core",
        },
        "sender": {
            "login": "testuser",
            "html_url": "https://github.com/testuser",
        },
        "pusher": {"name": "testuser"},
        "commits": [
            {
                "id": "abc123def456789",
                "message": "Test commit message",
            }
        ],
        "compare": "https://github.com/hydra-monitors/hm-core/compare/abc...def",
    }


@pytest.fixture
def sample_release_payload() -> dict:
    """Sample GitHub release event payload."""
    return {
        "action": "published",
        "release": {
            "id": 12345,
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "html_url": "https://github.com/hydra-monitors/hm-core/releases/tag/v1.0.0",
            "author": {
                "login": "releaseuser",
                "html_url": "https://github.com/releaseuser",
            },
        },
        "repository": {
            "full_name": "hydra-monitors/hm-core",
            "html_url": "https://github.com/hydra-monitors/hm-core",
        },
        "sender": {
            "login": "releaseuser",
            "html_url": "https://github.com/releaseuser",
        },
    }


@pytest.fixture
def sample_pr_payload() -> dict:
    """Sample GitHub pull_request event payload."""
    return {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Add new feature",
            "html_url": "https://github.com/hydra-monitors/hm-core/pull/42",
            "merged": False,
            "user": {
                "login": "prauthor",
                "html_url": "https://github.com/prauthor",
            },
        },
        "repository": {
            "full_name": "hydra-monitors/hm-core",
            "html_url": "https://github.com/hydra-monitors/hm-core",
        },
        "sender": {
            "login": "prauthor",
            "html_url": "https://github.com/prauthor",
        },
    }


@pytest.fixture
def sample_security_payload() -> dict:
    """Sample GitHub repository_vulnerability_alert event payload."""
    return {
        "alert": {
            "affected_package_name": "lodash",
            "affected_range": "< 4.17.21",
            "security_vulnerability": {
                "severity": "high",
                "summary": "Prototype Pollution in lodash",
            },
        },
        "repository": {
            "full_name": "hydra-monitors/hm-core",
            "html_url": "https://github.com/hydra-monitors/hm-core",
        },
        "sender": {
            "login": "github",
            "html_url": "https://github.com/github",
        },
    }


@pytest.fixture
def sample_dependabot_push_payload() -> dict:
    """Sample dependabot push event payload (should be filtered)."""
    return {
        "ref": "refs/heads/dependabot/npm_and_yarn/lodash-4.17.21",
        "after": "def456abc789",
        "repository": {
            "full_name": "hydra-monitors/hm-core",
            "html_url": "https://github.com/hydra-monitors/hm-core",
        },
        "sender": {
            "login": "dependabot[bot]",
            "html_url": "https://github.com/apps/dependabot",
        },
        "pusher": {"name": "dependabot[bot]"},
        "commits": [],
    }


@pytest.fixture
def mock_bot() -> AsyncMock:
    """Mock aiogram Bot instance."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot
