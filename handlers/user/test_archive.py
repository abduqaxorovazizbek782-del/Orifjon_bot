from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.engine import async_session
from database.models import TestArchive
from keyboards.buttons import BTN_TEST_ARCHIVE

router = Router()


@router.message(F.text == BTN_TEST_ARCHIVE)
async def show_tests(message: Message):
    async with async_session() as session:
        tests = (await session.scalars(
            select(TestArchive).order_by(TestArchive.created_at.desc()).limit(10))).all()
    if not tests:
        await message.answer("📊 Hozircha test natijasi yo'q.")
        return
    await message.answer(f"📊 Oxirgi {len(tests)} ta test natijasi:")
    for t in tests:
        cap = f"📌 {t.caption or '—'}\n🗓 {t.created_at.strftime('%Y-%m-%d %H:%M')}"
        try:
            if t.file_type == "photo":
                await message.bot.send_photo(message.chat.id, photo=t.file_id, caption=cap)
            else:
                await message.bot.send_document(message.chat.id, document=t.file_id, caption=cap)
        except Exception:
            await message.answer(f"⚠️ Fayl ochilmadi: {cap}")
