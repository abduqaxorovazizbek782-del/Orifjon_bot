from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import DebtFSM
from database.engine import async_session
from database.models import Student
from keyboards.reply import admin_menu
from keyboards.inline import students_select_kb
from keyboards.buttons import BTN_DEBT

router = Router()


@router.message(F.text == BTN_DEBT, F.from_user.id.in_(ADMINS))
async def debt_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("O'quvchi ism yoki familiyasini kiriting:")
    await state.set_state(DebtFSM.search)


@router.message(DebtFSM.search)
async def debt_search(message: Message, state: FSMContext):
    q = message.text.strip()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group)).where(or_(
                Student.name.ilike(f"%{q}%"), Student.last_name.ilike(f"%{q}%")))
        )).all()
    if not students:
        await message.answer("❌ Topilmadi. Qayta kiriting:")
        return
    await message.answer("Tanlang:", reply_markup=students_select_kb(students, "debt"))
    await state.set_state(DebtFSM.select)


@router.callback_query(DebtFSM.select, F.data.startswith("debt:"))
async def debt_pick(call: CallbackQuery, state: FSMContext):
    # Eski tugmani o'chiramiz (qayta bosilmasin)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.update_data(student_id=int(call.data.split(":")[1]))
    try:
        await call.message.edit_text("Eski qarz summasini kiriting:")
    except Exception:
        await call.message.answer("Eski qarz summasini kiriting:")
    await state.set_state(DebtFSM.amount)
    await call.answer()


@router.message(DebtFSM.amount)
async def debt_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(" ", "").replace(",", ""))
    except (ValueError, AttributeError):
        await message.answer("❌ Faqat raqam kiriting:")
        return
    data = await state.get_data()
    sid = data.get("student_id")
    if not sid:
        await message.answer("❌ Sessiya tugadi. «💸 Qarz yozish» dan qayta boshlang.",
                             reply_markup=admin_menu())
        await state.clear()
        return
    async with async_session() as session:
        student = await session.get(Student, sid)
        if not student:
            await message.answer("❌ O'quvchi topilmadi.", reply_markup=admin_menu())
            await state.clear()
            return
        student.balance -= amount
        await session.commit()
        nb, fn = student.balance, f"{student.name} {student.last_name}"
    await message.answer(f"✅ <b>{fn}</b> balansidan {amount:,.0f} so'm ayirildi.\n"
                         f"💰 Yangi balans: {nb:,.0f} so'm", reply_markup=admin_menu())
    await state.clear()
