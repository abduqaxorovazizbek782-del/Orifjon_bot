from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from states.states import UserCheckFSM
from database.engine import async_session
from database.models import Student
from keyboards.inline import students_select_kb
from keyboards.buttons import BTN_CHECK_BALANCE
from utils.helpers import group_label, safe_delete

router = Router()


@router.message(F.text == BTN_CHECK_BALANCE)
async def check_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ism yoki familiyani kiriting:")
    await state.set_state(UserCheckFSM.search)


@router.message(UserCheckFSM.search)
async def check_balance(message: Message, state: FSMContext):
    q = message.text.strip()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group)).where(or_(
                Student.name.ilike(f"%{q}%"), Student.last_name.ilike(f"%{q}%")))
        )).all()
    if not students:
        await message.answer("❌ Topilmadi. Qayta kiriting:")
        return
    if len(students) == 1:
        await _show(message, students[0])
        await state.clear()
        return
    await message.answer(f"🔍 {len(students)} ta topildi. Tanlang:",
                         reply_markup=students_select_kb(students, "balpick"))
    await state.set_state(UserCheckFSM.search)


async def _show(message: Message, s: Student):
    if s.balance < 0:
        await message.answer(
            f"👤 <b>{s.name} {s.last_name}</b>\n👥 {group_label(s)}\n"
            "━━━━━━━━━━━━━━\n⚠️ <b>Sizda qarz mavjud.</b>\n"
            "Iltimos, to'lovni o'z vaqtida amalga oshiring. 💳"
        )
    else:
        await message.answer(
            f"👤 <b>{s.name} {s.last_name}</b>\n👥 {group_label(s)}\n"
            "━━━━━━━━━━━━━━\n✅ <b>Qarzingiz yo'q.</b> Rahmat! 🎉"
        )


@router.callback_query(UserCheckFSM.search, F.data.startswith("balpick:"))
async def balance_pick(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[1])
    async with async_session() as session:
        s = await session.scalar(
            select(Student).options(selectinload(Student.group)).where(Student.id == sid))
    await safe_delete(call.message)
    if s:
        await _show(call.message, s)
    await state.clear()
    await call.answer()
