"""GitHub webhook signature verification (HMAC-SHA256)."""

import hashlib
import hmac
from collections.abc import Iterable


def _expected_signature(payload: bytes, secret: str) -> str:
    """Compute the expected `sha256=...` signature for a payload and secret."""
    return (
        "sha256="
        + hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
    )


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature against a single secret.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (e.g., "sha256=abc123...")
        secret: Webhook secret configured in GitHub

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not signature.startswith("sha256="):
        return False

    return hmac.compare_digest(_expected_signature(payload, secret), signature)


def verify_signature_any(payload: bytes, signature: str, secrets: Iterable[str]) -> bool:
    """
    Verify the signature against multiple secrets (multi-webhook support).

    A single bot endpoint can serve several GitHub webhooks (org- or repo-level),
    each signing with its own secret. The delivery is trusted if it matches any
    one of them. Comparison uses `hmac.compare_digest` per candidate.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value
        secrets: Configured webhook secrets to try

    Returns:
        True if the signature matches any non-empty secret, False otherwise
    """
    if not signature or not signature.startswith("sha256="):
        return False

    return any(
        hmac.compare_digest(_expected_signature(payload, secret), signature)
        for secret in secrets
        if secret
    )
