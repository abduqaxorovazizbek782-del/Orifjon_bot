import asyncio
import logging
from typing import Iterable

from aiogram import Bot
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest,
)

logger = logging.getLogger(__name__)

# Telegram ~30 msg/sec ruxsat beradi. Xavfsiz tomon uchun sekinroq.
RATE = 25            # soniyasiga nechta xabar
DELAY = 1.0 / RATE   # har xabar orasidagi pauza


async def _send_one(bot: Bot, chat_id: int, kind: str, file_id: str | None,
                    text: str) -> bool:
    """Bitta chatga yuboradi. FloodWait bo'lsa kutadi va qayta urinadi."""
    while True:
        try:
            if kind == "photo":
                await bot.send_photo(chat_id, photo=file_id, caption=text)
            elif kind == "document":
                await bot.send_document(chat_id, document=file_id, caption=text)
            else:
                await bot.send_message(chat_id, text)
            return True
        except TelegramRetryAfter as e:
            # Telegram "sekinla" dedi -> shuncha kutamiz va qayta urinamiz
            logger.warning("⏳ FloodWait: %ss kutilyapti...", e.retry_after)
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            # User botni bloklagan / guruhdan chiqarilgan
            return False
        except TelegramBadRequest:
            # Noto'g'ri chat_id yoki o'chgan xabar
            return False
        except Exception as e:
            logger.error("❌ Yuborishda xato (%s): %s", chat_id, e)
            return False


async def broadcast(
    bot: Bot,
    chat_ids: Iterable[int],
    text: str,
    kind: str = "text",        # "text" | "photo" | "document"
    file_id: str | None = None,
) -> tuple[int, int]:
    """Ko'p chatga xavfsiz, sekin yuboradi. (yuborildi, xato) qaytaradi."""
    sent, failed = 0, 0
    for chat_id in chat_ids:
        ok = await _send_one(bot, chat_id, kind, file_id, text)
        if ok:
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(DELAY)
    return sent, failed
