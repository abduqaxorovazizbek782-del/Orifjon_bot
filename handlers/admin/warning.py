from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config import ADMINS, GROUP_IDS
from states.states import WarningFSM
from database.engine import async_session
from database.models import BotUser
from utils.broadcast import broadcast

router = Router()


@router.message(Command("warning"), F.from_user.id.in_(ADMINS))
async def warning_start(message: Message, state: FSMContext):
    await message.answer("📢 E'lon matnini kiriting:")
    await state.set_state(WarningFSM.text)


@router.message(WarningFSM.text)
async def warning_send(message: Message, state: FSMContext):
    today = datetime.now().strftime("%Y-%m-%d")
    nice = ("📢 ━━━━━━━━━━━━━\n      <b>MUHIM E'LON</b>\n━━━━━━━━━━━━━ 📢\n\n"
            f"{message.text}\n\n🏫 <i>O'quv markazi ma'muriyati</i>\n🗓 {today}")

    async with async_session() as session:
        users = (await session.scalars(select(BotUser.tg_id))).all()

    await message.answer("📤 Yuborish boshlandi, kuting...")

    sent, failed = await broadcast(message.bot, users, nice, kind="text")
    gsent, gfailed = await broadcast(message.bot, GROUP_IDS, nice, kind="text")

    await message.answer(
        f"✅ Tarqatildi.\n"
        f"👤 Userlar: {sent} yuborildi, {failed} xato\n"
        f"👥 Guruhlar: {gsent} yuborildi, {gfailed} xato"
    )
    await state.clear()
