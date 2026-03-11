"""Tests for channel routing logic."""

from bot.models.config import ChannelConfig, Config
from bot.services.router import ChannelRouter


class TestChannelRouter:
    """Tests for ChannelRouter class."""

    def test_exact_match(self):
        """Test exact repo match."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=123,
                    repos=["org/repo"],
                    events=None,
                )
            ]
        )
        router = ChannelRouter(config)

        channels = router.find_channels("org/repo", "push")
        assert len(channels) == 1
        assert channels[0].chat_id == -1001234567890

    def test_no_match(self):
        """Test no matching repo."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=None,
                    repos=["org/repo1"],
                    events=None,
                )
            ]
        )
        router = ChannelRouter(config)

        channels = router.find_channels("org/repo2", "push")
        assert len(channels) == 0

    def test_wildcard_match(self):
        """Test org/* wildcard matching."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=None,
                    repos=["org/*"],
                    events=None,
                )
            ]
        )
        router = ChannelRouter(config)

        # Should match any repo in org
        assert len(router.find_channels("org/repo1", "push")) == 1
        assert len(router.find_channels("org/repo2", "push")) == 1
        assert len(router.find_channels("org/any-repo", "push")) == 1

        # Should not match different org
        assert len(router.find_channels("other-org/repo", "push")) == 0

    def test_event_filter(self):
        """Test event type filtering."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=None,
                    repos=["org/repo"],
                    events=["push", "release"],
                )
            ]
        )
        router = ChannelRouter(config)

        # Allowed events
        assert len(router.find_channels("org/repo", "push")) == 1
        assert len(router.find_channels("org/repo", "release")) == 1

        # Filtered events
        assert len(router.find_channels("org/repo", "pull_request")) == 0
        assert len(router.find_channels("org/repo", "security")) == 0

    def test_no_event_filter(self):
        """Test channel with no event filter (accepts all)."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=None,
                    repos=["org/repo"],
                    events=None,  # All events
                )
            ]
        )
        router = ChannelRouter(config)

        # Should accept all events
        assert len(router.find_channels("org/repo", "push")) == 1
        assert len(router.find_channels("org/repo", "release")) == 1
        assert len(router.find_channels("org/repo", "pull_request")) == 1
        assert len(router.find_channels("org/repo", "security")) == 1

    def test_multiple_channels(self):
        """Test routing to multiple channels."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001111111111,
                    thread_id=None,
                    repos=["org/repo"],
                    events=None,
                ),
                ChannelConfig(
                    chat_id=-1002222222222,
                    thread_id=None,
                    repos=["org/*"],
                    events=["security"],
                ),
            ]
        )
        router = ChannelRouter(config)

        # Push should only go to first channel
        push_channels = router.find_channels("org/repo", "push")
        assert len(push_channels) == 1
        assert push_channels[0].chat_id == -1001111111111

        # Security should go to both
        security_channels = router.find_channels("org/repo", "security")
        assert len(security_channels) == 2

    def test_multiple_repos_in_channel(self):
        """Test channel with multiple repo patterns."""
        config = Config(
            channels=[
                ChannelConfig(
                    chat_id=-1001234567890,
                    thread_id=None,
                    repos=["org1/repo1", "org2/repo2", "org3/*"],
                    events=None,
                )
            ]
        )
        router = ChannelRouter(config)

        assert len(router.find_channels("org1/repo1", "push")) == 1
        assert len(router.find_channels("org2/repo2", "push")) == 1
        assert len(router.find_channels("org3/any", "push")) == 1
        assert len(router.find_channels("org4/repo", "push")) == 0
