"""HTML message formatters for GitHub events."""

from html import escape

from bot.models.events import RepoBatch

# Severity emoji mapping
SEVERITY_EMOJI = {
    "critical": "\U0001f534",  # 🔴
    "high": "\U0001f7e0",  # 🟠
    "medium": "\U0001f7e1",  # 🟡
    "low": "\U0001f7e2",  # 🟢
    "unknown": "\u26aa",  # ⚪
}


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return escape(str(text), quote=False)


def link(url: str, text: str) -> str:
    """Create HTML link, fallback to plain text if no URL."""
    if url:
        return f'<a href="{escape(url)}">{escape_html(text)}</a>'
    return escape_html(text)


def truncate(text: str, max_len: int = 3900) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def format_push(payload: dict) -> tuple[str, str] | None:
    """
    Format push event message.

    Returns:
        (message, unique_key) or None if filtered
    """
    ref = payload.get("ref", "")
    if not ref.startswith("refs/heads/"):
        return None

    branch = ref.replace("refs/heads/", "")
    repo = payload["repository"]["full_name"]
    repo_url = payload["repository"]["html_url"]
    commits = payload.get("commits", [])
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]
    pusher = payload.get("pusher", {}).get("name", sender)
    pusher_url = f"https://github.com/{pusher}"

    msg = (
        f"\U0001f4dd Push to <b>{escape_html(repo)}</b> — "
        f"<code>{escape_html(branch)}</code> ({len(commits)} commit{'s' if len(commits) != 1 else ''})"
    )

    if commits:
        sha = commits[0]["id"][:7]
        commit_url = f"{repo_url}/commit/{commits[0]['id']}"
        msg += f"\n{link(commit_url, sha)}"

    if payload.get("compare"):
        msg += f"\n{link(payload['compare'], 'Compare diff')}"

    msg += f"\nRepo: {link(repo_url, repo)}"
    msg += f"\nSender: {link(sender_url, sender)}"
    msg += f"\nPusher: {link(pusher_url, pusher)}"
    msg += "\n\n#github"

    unique_key = f"push-{payload.get('after', 'unknown')}-{sender}"
    return truncate(msg), unique_key


def format_release(payload: dict) -> tuple[str, str] | None:
    """Format release event message."""
    release = payload.get("release", {})
    action = payload.get("action", "")

    tag = release.get("tag_name", "")
    name = release.get("name", tag)
    url = release.get("html_url", "")
    repo = payload["repository"]["full_name"]
    repo_url = payload["repository"]["html_url"]
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]
    author = release.get("author", {}).get("login", sender)
    author_url = release.get("author", {}).get("html_url", sender_url)

    msg = f"\U0001f680 Release <b>{escape_html(tag)}</b> in {link(repo_url, repo)}"
    if name and name != tag:
        msg += f"\nName: {escape_html(name)}"
    if url:
        msg += f"\n{link(url, 'Open release')}"
    msg += f"\nAuthor: {link(author_url, author)}"
    if sender != author:
        msg += f"\nSender: {link(sender_url, sender)}"
    msg += "\n\n#github"

    unique_key = f"release-{release.get('id', tag)}-{action}-{sender}"
    return truncate(msg), unique_key


def format_pr(payload: dict) -> tuple[str, str] | None:
    """Format pull_request event message."""
    pr = payload.get("pull_request", {})
    action = payload.get("action", "")

    # Only handle opened, closed, merged
    if action not in ("opened", "closed"):
        return None

    pr_num = pr.get("number", "?")
    pr_url = pr.get("html_url", "")
    pr_title = pr.get("title", "")
    repo = payload["repository"]["full_name"]
    repo_url = payload["repository"]["html_url"]
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]
    author = pr.get("user", {}).get("login", "unknown")
    author_url = pr.get("user", {}).get("html_url", "")

    # Determine emoji
    if sender == "dependabot[bot]":
        emoji = "\U0001f916"  # 🤖
    elif action == "opened":
        emoji = "\U0001f4cb"  # 📋
    elif action == "closed" and pr.get("merged"):
        emoji = "\u2705"  # ✅
        action = "merged"
    elif action == "closed":
        emoji = "\u274c"  # ❌
    else:
        emoji = "\U0001f504"  # 🔄

    msg = (
        f"{emoji} PR {escape_html(action)} #{escape_html(str(pr_num))} — "
        f"{escape_html(pr_title)}\n"
        f"{link(pr_url, 'Open PR')} · {link(repo_url, repo)}"
    )
    msg += f"\nAuthor: {link(author_url, author)}"
    if sender != author:
        msg += f"\nSender: {link(sender_url, sender)}"
    msg += "\n\n#github"

    unique_key = f"pull_request-{pr_num}-{action}-{sender}"
    return truncate(msg), unique_key


def format_review(payload: dict) -> tuple[str, str] | None:
    """Format pull_request_review event message."""
    review = payload.get("review", {})
    pr = payload.get("pull_request", {})

    state = (review.get("state") or "").lower()

    # Emoji based on state
    if state == "approved":
        emoji = "\u2705"  # ✅
    elif state == "changes_requested":
        emoji = "\u274c"  # ❌
    else:
        emoji = "\U0001f4ac"  # 💬

    pr_num = pr.get("number", "?")
    pr_title = pr.get("title", "")
    pr_url = pr.get("html_url", "")
    review_url = review.get("html_url", "")
    reviewer = review.get("user", {}).get("login", "unknown")
    reviewer_url = review.get("user", {}).get("html_url", "")
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]

    msg = (
        f"{emoji} Review {escape_html(state)} on #{escape_html(str(pr_num))} — "
        f"{escape_html(pr_title)}\n"
        f"{link(pr_url, 'Open PR')} · {link(review_url, 'Review')}"
    )
    msg += f"\nReviewer: {link(reviewer_url, reviewer)}"
    msg += f"\nSender: {link(sender_url, sender)}"
    msg += "\n\n#github"

    unique_key = f"pull_request_review-{review.get('id', 'unknown')}-{state}-{sender}"
    return truncate(msg), unique_key


def format_review_comment(payload: dict) -> tuple[str, str] | None:
    """Format pull_request_review_comment event message."""
    comment = payload.get("comment", {})
    pr = payload.get("pull_request", {})

    body = str(comment.get("body", ""))
    short = body[:100] + "..." if len(body) > 100 else body
    short = short.replace("\n", " ")

    pr_num = pr.get("number", "?")
    pr_title = pr.get("title", "")
    pr_url = pr.get("html_url", "")
    comment_url = comment.get("html_url", "")
    commenter = comment.get("user", {}).get("login", "unknown")
    commenter_url = comment.get("user", {}).get("html_url", "")
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]

    msg = (
        f"\U0001f4ac Review comment on #{escape_html(str(pr_num))} — "
        f"{escape_html(pr_title)}\n"
        f"{link(pr_url, 'Open PR')} · {link(comment_url, 'Comment')}"
    )
    msg += f"\nComment: {escape_html(short)}"
    msg += f"\nCommenter: {link(commenter_url, commenter)}"
    msg += f"\nSender: {link(sender_url, sender)}"
    msg += "\n\n#github"

    unique_key = f"pull_request_review_comment-{comment.get('id', 'unknown')}-{sender}"
    return truncate(msg), unique_key


def format_deploy_key(payload: dict) -> tuple[str, str] | None:
    """Format deploy_key event message."""
    key = payload.get("key", {})
    action = payload.get("action", "")

    title = key.get("title", "Untitled")
    repo = payload["repository"]["full_name"]
    repo_url = payload["repository"]["html_url"]
    sender = payload["sender"]["login"]
    sender_url = payload["sender"]["html_url"]

    msg = f"\U0001f511 Deploy key {escape_html(action)} in {link(repo_url, repo)}"
    msg += f"\nKey: {escape_html(title)}"
    msg += f"\nSender: {link(sender_url, sender)}"
    msg += "\n\n#github"

    unique_key = f"deploy_key-{key.get('id', title)}-{action}-{sender}"
    return truncate(msg), unique_key


def format_security_digest(repo_batch: RepoBatch) -> str:
    """
    Format security vulnerability digest message.

    Args:
        repo_batch: Batch of vulnerabilities for a repository

    Returns:
        Formatted HTML message
    """
    count = len(repo_batch.items)
    repo_name = repo_batch.repo_name
    repo_url = repo_batch.repo_url

    # Count by severity
    severity_counts: dict[str, int] = {}
    for item in repo_batch.items.values():
        sev = item.severity.lower()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Build severity lines
    severity_order = ["critical", "high", "medium", "low", "unknown"]
    severity_lines = []
    for sev in severity_order:
        if sev in severity_counts:
            emoji = SEVERITY_EMOJI.get(sev, "\u26aa")
            severity_lines.append(f"{emoji} {sev}: {severity_counts[sev]}")

    # Group by package
    by_package: dict[str, set[str]] = {}
    for item in repo_batch.items.values():
        if item.package_name not in by_package:
            by_package[item.package_name] = set()
        by_package[item.package_name].add(item.version)

    # Build details (max 25 packages)
    details = []
    packages = sorted(by_package.keys())
    for pkg in packages[:25]:
        versions = sorted(by_package[pkg])[:5]
        details.append(f"{escape_html(pkg)}@{escape_html('; '.join(versions))}")

    # Build message
    msg = (
        f"\U0001f6a8 Security Alert: {count} vulnerabilit{'ies' if count > 1 else 'y'} "
        f"detected in {link(repo_url, repo_name)}"
    )

    if severity_lines:
        msg += "\n\n" + "\n".join(severity_lines)

    if details:
        msg += "\n\n\U0001f4cb Details:"
        for i, detail in enumerate(details, 1):
            msg += f"\n{i}. {detail}"
        if len(packages) > 25:
            msg += f"\n\n…and {len(packages) - 25} more packages"

    msg += "\n\n#github #security"

    return truncate(msg)
