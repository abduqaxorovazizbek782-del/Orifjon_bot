from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.engine import async_session
from database.models import UploadedFile
from keyboards.buttons import BTN_FILES

router = Router()


@router.message(F.text == BTN_FILES)
async def show_files(message: Message):
    async with async_session() as session:
        files = (await session.scalars(
            select(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(10))).all()
    if not files:
        await message.answer("📂 Hozircha fayl yo'q.")
        return
    await message.answer(f"📂 Oxirgi {len(files)} ta fayl:")
    for f in files:
        cap = f"📌 {f.caption or '—'}\n🗓 {f.created_at.strftime('%Y-%m-%d')}"
        try:
            if f.file_type == "photo":
                await message.bot.send_photo(message.chat.id, photo=f.file_id, caption=cap)
            else:
                await message.bot.send_document(message.chat.id, document=f.file_id, caption=cap)
        except Exception:
            await message.answer(f"⚠️ Fayl ochilmadi: {cap}")
