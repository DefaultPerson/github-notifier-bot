"""FastAPI application factory."""

from typing import Any

from fastapi import FastAPI

from bot.webhook.handlers import router as webhook_router
from bot.webhook.health import router as health_router


def create_app(lifespan: Any = None) -> FastAPI:
    """
    Create FastAPI application with routers.

    Args:
        lifespan: Optional async context manager for app lifespan events

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="GitHub Notifier Bot",
        description="GitHub webhook to Telegram notifier",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(webhook_router)

    return app
