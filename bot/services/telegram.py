"""Telegram message sender using aiogram."""

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

logger = structlog.get_logger(__name__)


class TelegramSender:
    """Wrapper around aiogram Bot for sending messages."""

    def __init__(self, bot: Bot):
        """
        Initialize Telegram sender.

        Args:
            bot: aiogram Bot instance
        """
        self._bot = bot

    async def send(
        self,
        chat_id: int,
        text: str,
        thread_id: int | None = None,
    ) -> bool:
        """
        Send message to Telegram chat.

        Args:
            chat_id: Target chat ID
            text: Message text (HTML format)
            thread_id: Optional thread/topic ID

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self._bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=thread_id,
                disable_web_page_preview=True,
            )
            return True

        except TelegramRetryAfter as e:
            logger.warning(
                "rate_limited",
                chat_id=chat_id,
                retry_after=e.retry_after,
            )
            return False

        except TelegramForbiddenError:
            logger.error(
                "bot_blocked",
                chat_id=chat_id,
            )
            return False

        except TelegramBadRequest as e:
            logger.error(
                "bad_request",
                chat_id=chat_id,
                error=str(e),
            )
            return False

        except Exception as e:
            logger.error(
                "send_error",
                chat_id=chat_id,
                error=str(e),
            )
            return False
