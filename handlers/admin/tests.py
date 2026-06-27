from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from config import ADMINS
from states.states import TestFSM
from database.engine import async_session
from database.models import Student, TestResult, Group
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_TEST_UPLOAD
from utils.helpers import download_excel, safe_int, safe_float

router = Router()


@router.message(F.text == BTN_TEST_UPLOAD, F.from_user.id.in_(ADMINS))
async def ask_year(message: Message, state: FSMContext):
    await message.answer("📊 Test qaysi <b>o'quv yili</b> uchun? (masalan: 2025):")
    await state.set_state(TestFSM.year)


@router.message(TestFSM.year, F.text)
async def ask_file(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("❌ Yil noto'g'ri. Faqat raqam kiriting. Masalan: 2025")
        return
    year = int(raw)
    if not (2000 <= year <= 2100):
        await message.answer("❌ Yil 2000–2100 oralig'ida bo'lsin. Masalan: 2025")
        return
    await state.update_data(year=year)
    await message.answer("📊 Faylni yuboring.\nUstunlar: <code>student_id, score</code>")
    await state.set_state(TestFSM.file)


@router.message(TestFSM.year)
async def ask_year_invalid(message: Message):
    await message.answer("❌ Iltimos, yilni raqam ko'rinishida yozing. Masalan: 2025")


@router.message(TestFSM.file, F.document)
async def load_test(message: Message, state: FSMContext):
    data = await state.get_data()
    year = data["year"]
    df, err = await download_excel(message)
    if err:
        await message.answer(err)
        return
    if not {"student_id", "score"}.issubset(set(df.columns)):
        await message.answer("❌ Ustunlar: student_id, score bo'lishi kerak.")
        await state.clear()
        return

    async with async_session() as session:
        valid_ids = set((await session.scalars(
            select(Student.id).join(Group).where(Group.year == year)
        )).all())
        added, skipped, affected = 0, 0, set()
        for _, row in df.iterrows():
            sid, score = safe_int(row["student_id"]), safe_float(row["score"])
            if sid is None or score is None:
                skipped += 1
                continue
            if sid not in valid_ids:
                skipped += 1
                continue
            session.add(TestResult(student_id=sid, score=score))
            affected.add(sid); added += 1
        await session.flush()
        for sid in affected:
            avg = await session.scalar(
                select(func.avg(TestResult.score)).where(TestResult.student_id == sid))
            st = await session.get(Student, sid)
            st.average_score = round(avg or 0.0, 2)
        await session.commit()

    await message.answer(f"✅ {year}-yil: {added} ta natija yuklandi.\n"
                         f"⚠️ Boshqa yil/xato: {skipped}", reply_markup=admin_menu())
    await state.clear()


@router.message(TestFSM.file)
async def test_invalid(message: Message):
    await message.answer("❌ Iltimos, .xlsx faylni yuboring.")
