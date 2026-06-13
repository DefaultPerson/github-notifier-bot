"""Tests for Settings webhook-secret handling."""

import pytest
from pydantic import ValidationError

from bot.config.settings import Settings


def _settings(**overrides) -> Settings:
    """Build Settings with required fields, bypassing the environment."""
    base = {"bot_token": "test-token", "_env_file": None}
    base.update(overrides)
    return Settings(**base)


class TestWebhookSecrets:
    """Tests for the merged `webhook_secrets` property."""

    def test_single_legacy_secret(self):
        s = _settings(github_webhook_secret="alpha")
        assert s.webhook_secrets == ["alpha"]

    def test_list_only(self):
        s = _settings(github_webhook_secret=None, github_webhook_secrets="alpha,beta")
        assert s.webhook_secrets == ["alpha", "beta"]

    def test_merge_and_strip(self):
        s = _settings(
            github_webhook_secret="alpha",
            github_webhook_secrets=" beta , gamma ",
        )
        assert s.webhook_secrets == ["alpha", "beta", "gamma"]

    def test_dedup_preserves_order(self):
        s = _settings(
            github_webhook_secret="alpha",
            github_webhook_secrets="beta,alpha,gamma,beta",
        )
        assert s.webhook_secrets == ["alpha", "beta", "gamma"]

    def test_blank_entries_dropped(self):
        s = _settings(github_webhook_secret="alpha", github_webhook_secrets=",, ,beta,")
        assert s.webhook_secrets == ["alpha", "beta"]

    def test_requires_at_least_one_secret(self):
        with pytest.raises(ValidationError):
            _settings(github_webhook_secret=None, github_webhook_secrets="  ,  ")
