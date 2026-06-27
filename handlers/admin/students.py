from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import StudentFSM
from database.engine import async_session
from database.models import Student, Group
from keyboards.reply import admin_menu
from keyboards.inline import groups_kb, student_remove_kb, student_remove_confirm_kb
from keyboards.buttons import BTN_ADD_STUDENT, BTN_STUDENT_LIST
from utils.helpers import group_label, safe_delete

router = Router()


@router.message(F.text == BTN_ADD_STUDENT, F.from_user.id.in_(ADMINS))
async def add_student(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("O'quvchi ismini kiriting:")
    await state.set_state(StudentFSM.name)


@router.message(StudentFSM.name)
async def st_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Familiyasini kiriting:")
    await state.set_state(StudentFSM.last_name)


@router.message(StudentFSM.last_name)
async def st_last(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await message.answer("Telefon raqamini kiriting:")
    await state.set_state(StudentFSM.tel)


@router.message(StudentFSM.tel)
async def st_tel(message: Message, state: FSMContext):
    await state.update_data(tel=message.text.strip())
    async with async_session() as session:
        groups = (await session.scalars(select(Group))).all()
    if not groups:
        await message.answer("❌ Avval guruh yarating!", reply_markup=admin_menu())
        await state.clear()
        return
    await message.answer("Guruhni tanlang:", reply_markup=groups_kb(groups, "addst"))
    await state.set_state(StudentFSM.group_id)


@router.callback_query(StudentFSM.group_id, F.data.startswith("addst:"))
async def st_group(call: CallbackQuery, state: FSMContext):
    group_id = int(call.data.split(":")[1])
    data = await state.get_data()
    async with async_session() as session:
        session.add(Student(name=data["name"], last_name=data["last_name"],
                            tel=data["tel"], group_id=group_id, balance=0.0))
        await session.commit()
    await safe_delete(call.message)
    await call.message.answer("✅ O'quvchi qo'shildi.", reply_markup=admin_menu())
    await state.clear()
    await call.answer()


@router.message(F.text == BTN_STUDENT_LIST, F.from_user.id.in_(ADMINS))
async def list_students(message: Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
        )).all()
    if not students:
        await message.answer("Hozircha o'quvchilar yo'q.")
        return
    for s in students:
        text = (f"👤 <b>{s.name} {s.last_name}</b>\n📞 {s.tel}\n"
                f"👥 Guruh: {group_label(s)}\n💰 Balans: {s.balance:,.0f} so'm\n"
                f"🏆 O'rtacha: {s.average_score:.1f}%")
        await message.answer(text, reply_markup=student_remove_kb(s.id))


@router.callback_query(F.data.startswith("remove:"))
async def remove_ask(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    sid = int(call.data.split(":")[1])
    async with async_session() as session:
        s = await session.get(Student, sid)
    name = f"{s.name} {s.last_name}" if s else "o'quvchi"
    try:
        await call.message.edit_text(
            f"⚠️ <b>{name}</b> ni o'chirishni xohlaysizmi?\n"
            "Bu amalni ortga qaytarib bo'lmaydi.",
            reply_markup=student_remove_confirm_kb(sid)
        )
    except Exception:
        await call.message.answer(
            f"⚠️ <b>{name}</b> ni o'chirishni xohlaysizmi?",
            reply_markup=student_remove_confirm_kb(sid)
        )
    await call.answer()


@router.callback_query(F.data.startswith("delok:"))
async def remove_confirm(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    sid = int(call.data.split(":")[1])
    async with async_session() as session:
        s = await session.get(Student, sid)
        if s:
            # ORM cascade ishlashi uchun session.delete (test natijalari/davomat ham o'chadi)
            await session.delete(s)
            await session.commit()
    try:
        await call.message.edit_text("❌ O'quvchi o'chirildi.")
    except Exception:
        pass
    await call.answer("O'chirildi")


@router.callback_query(F.data.startswith("delno:"))
async def remove_cancel(call: CallbackQuery):
    try:
        await call.message.edit_text("✅ Bekor qilindi.")
    except Exception:
        pass
    await call.answer()
