"""Dependabot push spam filter."""


def is_dependabot_push_spam(payload: dict) -> bool:
    """
    Check if push event is dependabot spam (push to dependabot/* branch).

    We filter these because dependabot creates many branches that get merged
    quickly, and the actual PR events are more informative.

    Args:
        payload: GitHub push event payload

    Returns:
        True if this is dependabot spam that should be filtered
    """
    sender = payload.get("sender", {}).get("login", "")
    ref = payload.get("ref", "")

    # Check if sender is dependabot and pushing to dependabot branch
    is_dependabot_sender = sender == "dependabot[bot]"
    is_dependabot_branch = "dependabot/" in ref

    return is_dependabot_sender and is_dependabot_branch
