from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from states.states import RatingFSM, HistoryFSM
from database.engine import async_session
from database.models import Student, Attendance
from keyboards.inline import students_select_kb
from keyboards.buttons import BTN_RATING, BTN_HISTORY
from utils.helpers import safe_delete

router = Router()


@router.message(F.text == BTN_RATING)
async def rating_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("O'quvchi ism/familiyasini kiriting:")
    await state.set_state(RatingFSM.search)


@router.message(RatingFSM.search)
async def rating_search(message: Message, state: FSMContext):
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
        await _rating(message, students[0].id)
        await state.clear()
        return
    await message.answer(f"🔍 {len(students)} ta topildi. Tanlang:",
                         reply_markup=students_select_kb(students, "ratepick"))
    await state.set_state(RatingFSM.search)


async def _rating(message: Message, sid: int):
    async with async_session() as session:
        s = await session.get(Student, sid)
        if not s:
            await message.answer("❌ O'quvchi topilmadi.")
            return
        absents = await session.scalar(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == sid, Attendance.present == 0)
        ) or 0
    await message.answer(
        f"🏆 <b>{s.name} {s.last_name}</b>\n━━━━━━━━━━━━━━\n"
        f"📊 O'rtacha test: <b>{s.average_score:.1f}%</b>\n"
        f"🚫 Kelmagan kunlari: <b>{absents}</b> ta"
    )


@router.callback_query(RatingFSM.search, F.data.startswith("ratepick:"))
async def rating_pick(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[1])
    await safe_delete(call.message)
    await _rating(call.message, sid)
    await state.clear()
    await call.answer()


@router.message(F.text == BTN_HISTORY)
async def history_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("O'quvchi ism/familiyasini kiriting:")
    await state.set_state(HistoryFSM.search)


@router.message(HistoryFSM.search)
async def history_search(message: Message, state: FSMContext):
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
        await _history(message, students[0].id)
        await state.clear()
        return
    await message.answer(f"🔍 {len(students)} ta topildi. Tanlang:",
                         reply_markup=students_select_kb(students, "histpick"))
    await state.set_state(HistoryFSM.search)


async def _history(message: Message, sid: int):
    async with async_session() as session:
        s = await session.scalar(select(Student).options(
            selectinload(Student.test_results)).where(Student.id == sid))
    if not s or not s.test_results:
        await message.answer("📅 Test natijalari yo'q.")
        return
    res = sorted(s.test_results, key=lambda r: r.created_at, reverse=True)
    lines = [f"📅 <b>Testlar tarixi</b> — {s.name} {s.last_name}\n"]
    for r in res:
        lines.append(f"🗓 {r.created_at.strftime('%Y-%m-%d')} — {r.score:.0f}%")
    await message.answer("\n".join(lines))


@router.callback_query(HistoryFSM.search, F.data.startswith("histpick:"))
async def history_pick(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[1])
    await safe_delete(call.message)
    await _history(call.message, sid)
    await state.clear()
    await call.answer()
