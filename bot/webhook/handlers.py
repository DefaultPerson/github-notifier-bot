"""GitHub webhook handler endpoint."""

import structlog
from fastapi import APIRouter, HTTPException, Request

from bot.config.settings import settings
from bot.webhook.signature import verify_signature

router = APIRouter(tags=["webhook"])
logger = structlog.get_logger(__name__)

# GitHub event type to internal event type mapping
EVENT_MAP = {
    "repository_vulnerability_alert": "security",
    "release": "release",
    "push": "push",
    "pull_request": "pull_request",
    "pull_request_review": "review",
    "pull_request_review_comment": "review_comment",
    "deploy_key": "deploy_key",
}


@router.post("/webhook/github")
async def github_webhook(request: Request) -> dict[str, str]:
    """
    Handle incoming GitHub webhook events.

    Verifies signature, routes to appropriate handlers, and sends to Telegram.
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Verify signature
    if not verify_signature(body, signature, settings.github_webhook_secret):
        logger.warning("invalid_signature", signature=signature[:20] if signature else "missing")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Get event type
    event_type = request.headers.get("X-GitHub-Event", "")
    mapped_event = EVENT_MAP.get(event_type)

    if not mapped_event:
        logger.debug("ignored_event", gh_event=event_type)
        return {"status": "ignored", "reason": f"unsupported event: {event_type}"}

    # Parse payload
    payload = await request.json()
    repo = payload.get("repository", {}).get("full_name", "unknown")

    logger.info("webhook_received", gh_event=mapped_event, repo=repo)

    # Get services from app state
    channel_router = request.app.state.router
    dedup = request.app.state.dedup
    batcher = request.app.state.batcher
    sender = request.app.state.sender

    # Find target channels
    channels = channel_router.find_channels(repo, mapped_event)
    if not channels:
        logger.debug("no_matching_channels", repo=repo, gh_event=mapped_event)
        return {"status": "no_channels"}

    # Handle security alerts separately (batching)
    if mapped_event == "security":
        result = await handle_security_alert(payload, channels, batcher)
        return {"status": result}

    # Handle regular events
    result = await handle_regular_event(event_type, payload, channels, dedup, sender)
    return {"status": result}


async def handle_security_alert(payload: dict, channels: list, batcher) -> str:
    """Handle security vulnerability alerts with batching."""
    from bot.models.events import VulnerabilityItem

    alert = payload.get("alert", {})
    repo_name = payload.get("repository", {}).get("full_name", "unknown")
    repo_url = payload.get("repository", {}).get("html_url", "")

    # Extract vulnerability data
    package_name = alert.get("affected_package_name", "unknown")
    version = alert.get("affected_range", "unknown")
    security_vuln = alert.get("security_vulnerability", {})
    severity = (security_vuln.get("severity") or "unknown").lower()
    summary = security_vuln.get("summary", "No summary")

    item = VulnerabilityItem(
        package_name=package_name,
        version=version,
        severity=severity,
        summary=summary,
    )

    # Add to batcher for each channel
    for channel in channels:
        await batcher.add(repo_name, repo_url, item, channel)

    logger.info(
        "security_alert_batched",
        repo=repo_name,
        package=package_name,
        severity=severity,
        channels=len(channels),
    )
    return "batched"


async def handle_regular_event(
    event_type: str,
    payload: dict,
    channels: list,
    dedup,
    sender,
) -> str:
    """Handle regular (non-security) GitHub events."""
    from bot.filters.dependabot import is_dependabot_push_spam
    from bot.services import formatter

    # Filter dependabot spam
    if event_type == "push" and is_dependabot_push_spam(payload):
        logger.debug("filtered_dependabot_push")
        return "filtered_dependabot"

    # Get formatter for this event type
    format_fn = {
        "push": formatter.format_push,
        "release": formatter.format_release,
        "pull_request": formatter.format_pr,
        "pull_request_review": formatter.format_review,
        "pull_request_review_comment": formatter.format_review_comment,
        "deploy_key": formatter.format_deploy_key,
    }.get(event_type)

    if not format_fn:
        return "unsupported"

    result = format_fn(payload)
    if not result:
        return "filtered"

    message, unique_key = result

    # Dedup check
    if not dedup.add_if_new(unique_key):
        logger.debug("duplicate_message", key=unique_key)
        return "duplicate"

    # Send to all matching channels
    for channel in channels:
        await sender.send(
            chat_id=channel.chat_id,
            text=message,
            thread_id=channel.thread_id,
        )

    logger.info(
        "message_sent",
        gh_event=event_type,
        channels=len(channels),
        key=unique_key,
    )
    return "sent"
