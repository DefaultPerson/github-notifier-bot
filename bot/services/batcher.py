"""Security alert batching with configurable flush window."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

from bot.models.config import ChannelConfig
from bot.models.events import RepoBatch, VulnerabilityItem

logger = structlog.get_logger(__name__)


@dataclass
class ChannelBatch:
    """Batch for a specific channel."""

    channel: ChannelConfig
    repos: dict[str, RepoBatch] = field(default_factory=dict)


class SecurityBatcher:
    """Batches security alerts per channel with configurable flush window."""

    def __init__(
        self,
        window_seconds: float,
        on_flush: Callable[[ChannelConfig, RepoBatch], Awaitable[None]],
    ):
        """
        Initialize security batcher.

        Args:
            window_seconds: Time to wait before flushing batch
            on_flush: Async callback to send the batched message
        """
        self._window = window_seconds
        self._on_flush = on_flush
        self._batches: dict[int, ChannelBatch] = {}  # chat_id -> batch
        self._flush_tasks: dict[str, asyncio.Task[Any]] = {}  # "chat_id:repo" -> task
        self._lock = asyncio.Lock()

    async def add(
        self,
        repo_name: str,
        repo_url: str,
        item: VulnerabilityItem,
        channel: ChannelConfig,
    ) -> None:
        """
        Add vulnerability item to batch for the given channel.

        Args:
            repo_name: Repository full name
            repo_url: Repository URL
            item: Vulnerability item to add
            channel: Target channel configuration
        """
        async with self._lock:
            now = asyncio.get_event_loop().time()
            batch_key = f"{channel.chat_id}:{repo_name}"

            # Initialize channel batch if needed
            if channel.chat_id not in self._batches:
                self._batches[channel.chat_id] = ChannelBatch(channel=channel)

            channel_batch = self._batches[channel.chat_id]

            # Initialize repo batch if needed
            if repo_name not in channel_batch.repos:
                channel_batch.repos[repo_name] = RepoBatch(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    items={},
                    first_at=now,
                    last_at=now,
                )
                # Schedule flush for this repo
                self._flush_tasks[batch_key] = asyncio.create_task(
                    self._schedule_flush(channel.chat_id, repo_name)
                )

            repo_batch = channel_batch.repos[repo_name]
            repo_batch.last_at = now

            # Add item if not duplicate
            if item.unique_key not in repo_batch.items:
                repo_batch.items[item.unique_key] = item
                logger.debug(
                    "vulnerability_added",
                    repo=repo_name,
                    package=item.package_name,
                    chat_id=channel.chat_id,
                )

    async def _schedule_flush(self, chat_id: int, repo_name: str) -> None:
        """Wait for window and flush the batch."""
        await asyncio.sleep(self._window)

        async with self._lock:
            batch_key = f"{chat_id}:{repo_name}"

            if chat_id not in self._batches:
                return

            channel_batch = self._batches[chat_id]
            if repo_name not in channel_batch.repos:
                return

            repo_batch = channel_batch.repos.pop(repo_name)
            self._flush_tasks.pop(batch_key, None)

            # Clean up empty channel batch
            if not channel_batch.repos:
                del self._batches[chat_id]

        # Send the digest
        if repo_batch.items:
            await self._on_flush(channel_batch.channel, repo_batch)

    async def flush_all(self) -> None:
        """Flush all pending batches (for graceful shutdown)."""
        async with self._lock:
            # Cancel all scheduled flushes
            for task in self._flush_tasks.values():
                task.cancel()

            # Collect all pending batches
            pending: list[tuple[ChannelConfig, RepoBatch]] = []
            for channel_batch in self._batches.values():
                for repo_batch in channel_batch.repos.values():
                    if repo_batch.items:
                        pending.append((channel_batch.channel, repo_batch))

            self._batches.clear()
            self._flush_tasks.clear()

        # Flush all pending
        for channel, repo_batch in pending:
            try:
                await self._on_flush(channel, repo_batch)
            except Exception as e:
                logger.error("flush_error", error=str(e), repo=repo_batch.repo_name)
