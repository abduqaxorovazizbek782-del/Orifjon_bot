from sqlalchemy import select

from database.engine import async_session
from database.models import PaymentCard
from config import cards_text as _default_cards_text

MAX_CARDS = 4


async def get_cards() -> list[PaymentCard]:
    async with async_session() as session:
        return (await session.scalars(
            select(PaymentCard).order_by(PaymentCard.id)
        )).all()


async def cards_text_db() -> str:
    """Bazadagi kartalar matni. Baza bo'sh bo'lsa — eski (config) kartalar."""
    cards = await get_cards()
    if not cards:
        return _default_cards_text()
    lines = ["💳 <b>To'lov uchun karta ma'lumotlari:</b>\n"]
    for c in cards:
        tel = f"📞 {c.tel}\n" if c.tel else ""
        lines.append(f"🧑 {c.name}\n💳 <code>{c.card}</code>\n{tel}")
    return "\n".join(lines)
