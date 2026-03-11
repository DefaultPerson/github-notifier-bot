"""Tests for message formatters."""

from bot.models.events import RepoBatch, VulnerabilityItem
from bot.services import formatter


class TestFormatPush:
    """Tests for format_push function."""

    def test_basic_push(self, sample_push_payload):
        """Test formatting a basic push event."""
        result = formatter.format_push(sample_push_payload)

        assert result is not None
        message, unique_key = result

        assert "Push to" in message
        assert "hydra-monitors/hm-core" in message
        assert "main" in message
        assert "testuser" in message
        assert "#github" in message
        assert unique_key.startswith("push-")

    def test_push_to_tag_filtered(self, sample_push_payload):
        """Test that pushes to tags are filtered."""
        sample_push_payload["ref"] = "refs/tags/v1.0.0"
        result = formatter.format_push(sample_push_payload)

        assert result is None

    def test_push_html_escaping(self, sample_push_payload):
        """Test that special characters are escaped."""
        sample_push_payload["repository"]["full_name"] = "org/<script>test"
        result = formatter.format_push(sample_push_payload)

        assert result is not None
        message, _ = result
        assert "<script>" not in message
        assert "&lt;script&gt;" in message


class TestFormatRelease:
    """Tests for format_release function."""

    def test_basic_release(self, sample_release_payload):
        """Test formatting a basic release event."""
        result = formatter.format_release(sample_release_payload)

        assert result is not None
        message, unique_key = result

        assert "Release" in message
        assert "v1.0.0" in message
        assert "hydra-monitors/hm-core" in message
        assert "#github" in message
        assert "release-" in unique_key


class TestFormatPR:
    """Tests for format_pr function."""

    def test_opened_pr(self, sample_pr_payload):
        """Test formatting an opened PR."""
        result = formatter.format_pr(sample_pr_payload)

        assert result is not None
        message, unique_key = result

        assert "PR opened" in message
        assert "#42" in message
        assert "Add new feature" in message
        assert "#github" in message

    def test_merged_pr(self, sample_pr_payload):
        """Test formatting a merged PR."""
        sample_pr_payload["action"] = "closed"
        sample_pr_payload["pull_request"]["merged"] = True

        result = formatter.format_pr(sample_pr_payload)

        assert result is not None
        message, unique_key = result
        assert "PR merged" in message
        assert "✅" in message

    def test_closed_pr(self, sample_pr_payload):
        """Test formatting a closed (not merged) PR."""
        sample_pr_payload["action"] = "closed"
        sample_pr_payload["pull_request"]["merged"] = False

        result = formatter.format_pr(sample_pr_payload)

        assert result is not None
        message, _ = result
        assert "PR closed" in message
        assert "❌" in message

    def test_unsupported_action_filtered(self, sample_pr_payload):
        """Test that unsupported PR actions are filtered."""
        sample_pr_payload["action"] = "edited"
        result = formatter.format_pr(sample_pr_payload)

        assert result is None


class TestFormatSecurityDigest:
    """Tests for format_security_digest function."""

    def test_single_vulnerability(self):
        """Test formatting a single vulnerability."""
        batch = RepoBatch(
            repo_name="org/repo",
            repo_url="https://github.com/org/repo",
            items={
                "lodash|<4.17.21|high": VulnerabilityItem(
                    package_name="lodash",
                    version="<4.17.21",
                    severity="high",
                    summary="Prototype Pollution",
                )
            },
            first_at=1000.0,
            last_at=1000.0,
        )

        message = formatter.format_security_digest(batch)

        assert "Security Alert" in message
        assert "1 vulnerability" in message
        assert "org/repo" in message
        assert "lodash" in message
        assert "🟠" in message  # high severity
        assert "#security" in message

    def test_multiple_vulnerabilities(self):
        """Test formatting multiple vulnerabilities."""
        batch = RepoBatch(
            repo_name="org/repo",
            repo_url="https://github.com/org/repo",
            items={
                "lodash|<4.17.21|high": VulnerabilityItem(
                    package_name="lodash",
                    version="<4.17.21",
                    severity="high",
                    summary="Prototype Pollution",
                ),
                "axios|<0.21.1|critical": VulnerabilityItem(
                    package_name="axios",
                    version="<0.21.1",
                    severity="critical",
                    summary="SSRF vulnerability",
                ),
            },
            first_at=1000.0,
            last_at=1000.0,
        )

        message = formatter.format_security_digest(batch)

        assert "2 vulnerabilities" in message
        assert "🔴" in message  # critical
        assert "🟠" in message  # high


class TestEscapeHtml:
    """Tests for HTML escaping."""

    def test_escape_special_chars(self):
        """Test that special characters are escaped."""
        assert formatter.escape_html("<script>") == "&lt;script&gt;"
        assert formatter.escape_html("a & b") == "a &amp; b"
        assert formatter.escape_html("test") == "test"


class TestTruncate:
    """Tests for message truncation."""

    def test_short_message(self):
        """Test that short messages are not truncated."""
        msg = "Short message"
        assert formatter.truncate(msg, 100) == msg

    def test_long_message(self):
        """Test that long messages are truncated."""
        msg = "x" * 100
        result = formatter.truncate(msg, 50)

        assert len(result) == 50
        assert result.endswith("…")
