"""Main entry point for the GitHub Notifier Bot."""

import asyncio
import signal
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI

from bot.config.channels import load_config_from_env, load_config_from_file
from bot.config.settings import settings
from bot.core.logger import configure_logging, get_logger
from bot.models.config import ChannelConfig
from bot.models.events import RepoBatch
from bot.services.batcher import SecurityBatcher
from bot.services.dedup import TTLCache
from bot.services.formatter import format_security_digest
from bot.services.router import ChannelRouter
from bot.services.telegram import TelegramSender
from bot.webhook.app import create_app

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle."""
    logger.info("starting", host=settings.host, port=settings.port)

    # Initialize Telegram bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    # Load channels config (from env or file)
    if settings.channel_chat_id and settings.channel_repos:
        config = load_config_from_env(
            settings.channel_chat_id,
            settings.channel_thread_id,
            settings.channel_repos,
        )
    else:
        config = load_config_from_file(settings.config_path)
    logger.info("config_loaded", channels=len(config.channels))

    # Initialize services
    channel_router = ChannelRouter(config)
    dedup = TTLCache(ttl_seconds=settings.dedup_ttl_seconds)
    sender = TelegramSender(bot)

    async def on_security_flush(channel: ChannelConfig, repo_batch: RepoBatch) -> None:
        """Callback for security batcher flush."""
        message = format_security_digest(repo_batch)
        unique_key = f"security-digest-{repo_batch.repo_name}-{int(repo_batch.first_at)}"

        if dedup.add_if_new(unique_key):
            await sender.send(
                chat_id=channel.chat_id,
                text=message,
                thread_id=channel.thread_id,
            )
            logger.info(
                "security_digest_sent",
                repo=repo_batch.repo_name,
                vulnerabilities=len(repo_batch.items),
                chat_id=channel.chat_id,
            )

    batcher = SecurityBatcher(
        window_seconds=settings.security_batch_window_seconds,
        on_flush=on_security_flush,
    )

    # Store in app state for dependency injection
    app.state.bot = bot
    app.state.router = channel_router
    app.state.dedup = dedup
    app.state.batcher = batcher
    app.state.sender = sender

    logger.info("bot_ready")

    yield

    # Graceful shutdown
    logger.info("shutting_down")
    await batcher.flush_all()
    await bot.session.close()
    logger.info("shutdown_complete")


def main() -> None:
    """Run the bot."""
    configure_logging(settings.log_level)
    logger.info("github_notifier_bot", version="0.1.0")

    app = create_app(lifespan)

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Handle SIGTERM for graceful shutdown (Kubernetes)
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(server.shutdown()))

    try:
        loop.run_until_complete(server.serve())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
