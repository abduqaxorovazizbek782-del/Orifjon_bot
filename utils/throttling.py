import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    """Bir user juda tez xabar yuborsa, ortiqchasini tashlab yuboradi."""

    def __init__(self, rate: float = 0.5):
        self.rate = rate          # soniya: shu vaqt ichida 1 ta xabarga ruxsat
        self._last: dict[int, float] = {}
        super().__init__()

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last.get(user.id, 0.0)
        if now - last < self.rate:
            # Juda tez — e'tiborsiz qoldiramiz (lekin callbackga javob beramiz)
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer()
                except Exception:
                    pass
            return  # handler chaqirilmaydi

        self._last[user.id] = now
        return await handler(event, data)
