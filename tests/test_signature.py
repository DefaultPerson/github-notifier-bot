"""Tests for GitHub webhook signature verification."""

import hashlib
import hmac

from bot.webhook.signature import verify_signature, verify_signature_any


class TestVerifySignature:
    """Tests for verify_signature function."""

    def test_valid_signature(self):
        """Test that valid signature is accepted."""
        payload = b'{"test": "data"}'
        secret = "test-secret"

        # Generate valid signature
        expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        assert verify_signature(payload, expected, secret) is True

    def test_invalid_signature(self):
        """Test that invalid signature is rejected."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        invalid_sig = "sha256=invalidhash123"

        assert verify_signature(payload, invalid_sig, secret) is False

    def test_missing_signature(self):
        """Test that missing signature is rejected."""
        payload = b'{"test": "data"}'
        secret = "test-secret"

        assert verify_signature(payload, "", secret) is False
        assert verify_signature(payload, None, secret) is False  # type: ignore

    def test_wrong_prefix(self):
        """Test that non-sha256 signature is rejected."""
        payload = b'{"test": "data"}'
        secret = "test-secret"

        # sha1 prefix instead of sha256
        assert verify_signature(payload, "sha1=abc123", secret) is False

    def test_different_payload(self):
        """Test that signature for different payload is rejected."""
        payload1 = b'{"test": "data1"}'
        payload2 = b'{"test": "data2"}'
        secret = "test-secret"

        # Generate signature for payload1
        sig = "sha256=" + hmac.new(secret.encode(), payload1, hashlib.sha256).hexdigest()

        # Try to verify with payload2
        assert verify_signature(payload2, sig, secret) is False

    def test_different_secret(self):
        """Test that signature with different secret is rejected."""
        payload = b'{"test": "data"}'
        secret1 = "secret1"
        secret2 = "secret2"

        # Generate signature with secret1
        sig = "sha256=" + hmac.new(secret1.encode(), payload, hashlib.sha256).hexdigest()

        # Try to verify with secret2
        assert verify_signature(payload, sig, secret2) is False


class TestVerifySignatureAny:
    """Tests for verify_signature_any (multi-secret) function."""

    @staticmethod
    def _sign(payload: bytes, secret: str) -> str:
        return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    def test_matches_first_secret(self):
        """Accept a signature produced with the first configured secret."""
        payload = b'{"test": "data"}'
        secrets = ["secret-a", "secret-b", "secret-c"]
        sig = self._sign(payload, "secret-a")

        assert verify_signature_any(payload, sig, secrets) is True

    def test_matches_later_secret(self):
        """Accept a signature produced with a non-first secret."""
        payload = b'{"test": "data"}'
        secrets = ["secret-a", "secret-b", "secret-c"]
        sig = self._sign(payload, "secret-c")

        assert verify_signature_any(payload, sig, secrets) is True

    def test_matches_no_secret(self):
        """Reject a signature that matches none of the secrets."""
        payload = b'{"test": "data"}'
        secrets = ["secret-a", "secret-b"]
        sig = self._sign(payload, "other-secret")

        assert verify_signature_any(payload, sig, secrets) is False

    def test_empty_secrets(self):
        """Reject when no secrets are configured."""
        payload = b'{"test": "data"}'
        sig = self._sign(payload, "secret-a")

        assert verify_signature_any(payload, sig, []) is False

    def test_skips_empty_secret_values(self):
        """Empty/blank secret entries are ignored, not treated as a match."""
        payload = b'{"test": "data"}'
        sig = self._sign(payload, "secret-a")

        # Empty strings must never validate; a real match still passes.
        assert verify_signature_any(payload, sig, ["", "secret-a"]) is True
        assert verify_signature_any(payload, sig, ["", "  "]) is False

    def test_missing_signature(self):
        """Reject missing or wrong-prefix signatures regardless of secrets."""
        payload = b'{"test": "data"}'
        secrets = ["secret-a"]

        assert verify_signature_any(payload, "", secrets) is False
        assert verify_signature_any(payload, "sha1=abc123", secrets) is False
