from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import YearFSM
from database.engine import async_session
from database.models import Group
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_YEAR_GROUPS

router = Router()


@router.message(F.text == BTN_YEAR_GROUPS, F.from_user.id.in_(ADMINS))
async def year_start(message: Message, state: FSMContext):
    await message.answer("Qaysi o'quv yili? (masalan: 2024):")
    await state.set_state(YearFSM.year)


@router.message(YearFSM.year)
async def year_show(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Yil noto'g'ri. Masalan: 2024")
        return
    async with async_session() as session:
        groups = (await session.scalars(
            select(Group).options(selectinload(Group.students)).where(Group.year == year)
        )).all()
    if not groups:
        await message.answer(f"🗓 {year}-yil uchun guruh topilmadi.", reply_markup=admin_menu())
        await state.clear()
        return
    await message.answer(f"🗂 <b>{year}-o'quv yili</b> guruhlari:")
    for g in groups:
        lines = [f"📁 <b>{g.name}</b> (ID: {g.id})",
                 f"💰 Oylik: {g.monthly_price:,.0f} so'm",
                 f"👥 Soni: {len(g.students)}"]
        if g.students:
            lines.append("\n<b>Ro'yxat:</b>")
            for i, s in enumerate(g.students, 1):
                lines.append(f"{i}. {s.name} {s.last_name} — ball: {s.average_score:.1f}%")
        await message.answer("\n".join(lines))
    await message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
