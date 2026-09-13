"""Tests for the channel config loaders (env vars and YAML file)."""

import pytest

from bot.config.channels import load_config_from_env, load_config_from_file


class TestLoadConfigFromEnv:
    def test_single_destination_defaults(self):
        config = load_config_from_env(1244608389, 636135, "*")

        assert len(config.channels) == 1
        channel = config.channels[0]
        assert channel.chat_id == 1244608389
        assert channel.thread_id == 636135
        assert channel.repos == ["*"]
        assert channel.events is None
        assert channel.exclude_events is None

    def test_repos_split_and_stripped(self):
        config = load_config_from_env(-100, None, " org/*, org/repo ,,")
        assert config.channels[0].repos == ["org/*", "org/repo"]

    def test_events_and_exclude_events(self):
        config = load_config_from_env(
            -100, None, "*", events="push, release", exclude_events="security"
        )
        channel = config.channels[0]
        assert channel.events == ["push", "release"]
        assert channel.exclude_events == ["security"]

    def test_blank_event_lists_mean_unset(self):
        config = load_config_from_env(-100, None, "*", events=" , ", exclude_events="")
        channel = config.channels[0]
        assert channel.events is None
        assert channel.exclude_events is None

    def test_unknown_event_type_rejected(self):
        with pytest.raises(ValueError):
            load_config_from_env(-100, None, "*", exclude_events="bogus")


class TestLoadConfigFromFile:
    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config_from_file(tmp_path / "nope.yaml")

    def test_empty_channel_list_rejected(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("channels: []\n")
        with pytest.raises(ValueError, match="No channels configured"):
            load_config_from_file(path)

    def test_loads_channels(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(
            "channels:\n"
            "  - chat_id: -100\n"
            "    thread_id: 7\n"
            "    repos: [org/*]\n"
            "    exclude_events: [security]\n"
        )
        config = load_config_from_file(path)
        assert len(config.channels) == 1
        assert config.channels[0].exclude_events == ["security"]

    def test_baked_fallback_file_is_rejected_without_env(self):
        """The image's config.yaml must not silently route to nowhere."""
        with pytest.raises(ValueError, match="No channels configured"):
            load_config_from_file("config.yaml")
