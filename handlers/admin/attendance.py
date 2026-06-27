from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import AttendanceFSM
from database.engine import async_session
from database.models import Student, Group, Attendance
from keyboards.reply import admin_menu
from keyboards.inline import (
    groups_kb, attendance_mode_kb, attendance_marking_kb, attendance_confirm_kb,
)
from keyboards.buttons import BTN_ATTENDANCE
from utils.helpers import download_excel, safe_int

router = Router()


# ───────────── 1. Yil so'rash ─────────────

@router.message(F.text == BTN_ATTENDANCE, F.from_user.id.in_(ADMINS))
async def att_start(message: Message, state: FSMContext):
    await message.answer("🗓 Davomat qaysi <b>o'quv yili</b> uchun? (masalan: 2025):")
    await state.set_state(AttendanceFSM.year)


@router.message(AttendanceFSM.year)
async def att_year(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit() or not (2000 <= int(raw) <= 2100):
        await message.answer("❌ Yil noto'g'ri. Masalan: 2025")
        return
    year = int(raw)
    async with async_session() as session:
        groups = (await session.scalars(
            select(Group).where(Group.year == year)
        )).all()
    if not groups:
        await message.answer(f"❌ {year}-yil uchun guruh topilmadi.", reply_markup=admin_menu())
        await state.clear()
        return
    await state.update_data(year=year)
    await message.answer("Guruhni tanlang:", reply_markup=groups_kb(groups, "attgrp"))
    await state.set_state(AttendanceFSM.group)


# ───────────── 2. Guruh tanlash ─────────────

@router.callback_query(AttendanceFSM.group, F.data.startswith("attgrp:"))
async def att_group(call: CallbackQuery, state: FSMContext):
    group_id = int(call.data.split(":")[1])
    await state.update_data(group_id=group_id)
    try:
        await call.message.edit_text(
            "Davomat usulini tanlang:", reply_markup=attendance_mode_kb())
    except Exception:
        await call.message.answer(
            "Davomat usulini tanlang:", reply_markup=attendance_mode_kb())
    await state.set_state(AttendanceFSM.mode)
    await call.answer()


# ───────────── 3a. Bittalab rejim ─────────────

@router.callback_query(AttendanceFSM.mode, F.data == "att_mode:one")
async def att_mode_one(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).where(Student.group_id == data["group_id"])
            .order_by(Student.name)
        )).all()
    if not students:
        await call.message.edit_text("❌ Bu guruhda o'quvchi yo'q.")
        await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
        await state.clear()
        await call.answer()
        return

    await state.update_data(absent_ids=[])
    students_min = [{"id": s.id, "name": s.name, "last_name": s.last_name} for s in students]
    await state.update_data(students=students_min)

    await call.message.edit_text(
        "👥 <b>Davomat — kelmaganlarni belgilang</b>\n"
        "━━━━━━━━━━━━━━\n"
        "✅ = keldi, ❌ = kelmadi.\n"
        "Kelmagan o'quvchi ustiga bosing, so'ng «💾 Saqlash».",
        reply_markup=attendance_marking_kb(students, set()),
    )
    await state.set_state(AttendanceFSM.marking)
    await call.answer()


def _objs(students_min):
    """Dict ro'yxatini klaviatura uchun soxta obyektlarga aylantiradi."""
    class _S:
        def __init__(self, d):
            self.id = d["id"]; self.name = d["name"]; self.last_name = d["last_name"]
    return [_S(d) for d in students_min]


@router.callback_query(AttendanceFSM.marking, F.data.startswith("att_toggle:"))
async def att_toggle(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[1])
    data = await state.get_data()
    absent = set(data.get("absent_ids", []))
    if sid in absent:
        absent.discard(sid)
    else:
        absent.add(sid)
    await state.update_data(absent_ids=list(absent))
    students = _objs(data["students"])
    try:
        await call.message.edit_reply_markup(
            reply_markup=attendance_marking_kb(students, absent))
    except Exception:
        pass
    await call.answer()


@router.callback_query(AttendanceFSM.marking, F.data == "att_save")
async def att_save_ask(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    absent = data.get("absent_ids", [])
    total = len(data["students"])
    came = total - len(absent)
    await call.message.edit_text(
        "❓ <b>Davomatni saqlaymizmi?</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"✅ Kelgan: <b>{came}</b>\n"
        f"❌ Kelmagan: <b>{len(absent)}</b>\n"
        f"📅 Sana: <b>{date.today().isoformat()}</b>",
        reply_markup=attendance_confirm_kb(),
    )
    await state.set_state(AttendanceFSM.confirm)
    await call.answer()


@router.callback_query(AttendanceFSM.marking, F.data == "att_cancel")
async def att_cancel(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.edit_text("🚫 Davomat bekor qilindi.")
    except Exception:
        pass
    await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
    await call.answer()


@router.callback_query(AttendanceFSM.confirm, F.data == "att_confirm_yes")
async def att_confirm_yes(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    absent = set(data.get("absent_ids", []))
    students = data["students"]
    today = date.today()

    async with async_session() as session:
        for s in students:
            sid = s["id"]
            present = 0 if sid in absent else 1
            existing = await session.scalar(
                select(Attendance).where(
                    Attendance.student_id == sid, Attendance.day == today)
            )
            if existing:
                existing.present = present
            else:
                session.add(Attendance(student_id=sid, day=today, present=present))
        await session.commit()

    try:
        await call.message.edit_text(
            "✅ <b>Davomat saqlandi.</b>\n"
            f"📅 Sana: {today.isoformat()}\n"
            f"❌ Kelmaganlar: {len(absent)} ta"
        )
    except Exception:
        pass
    await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
    await call.answer()


@router.callback_query(AttendanceFSM.confirm, F.data == "att_confirm_no")
async def att_confirm_no(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.edit_text("🚫 Bekor qilindi. Davomat saqlanmadi.")
    except Exception:
        pass
    await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
    await call.answer()


# ───────────── 3b. Excel rejim ─────────────

@router.callback_query(AttendanceFSM.mode, F.data == "att_mode:excel")
async def att_mode_excel(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.edit_text(
            "📥 Davomat .xlsx faylini yuboring.\n"
            "Ustunlar: <code>sana, student_id, group, ism, familya</code>\n"
            "• <b>sana</b> — YYYY-MM-DD (masalan 2025-06-15)\n"
            "• <b>status</b> ustuni bo'lsa: 1=keldi, 0=kelmadi. "
            "Bo'lmasa, faylda bo'lganlar kelgan hisoblanadi."
        )
    except Exception:
        await call.message.answer("📥 Davomat .xlsx faylini yuboring.")
    await state.set_state(AttendanceFSM.file)
    await call.answer()


@router.message(AttendanceFSM.file, F.document)
async def att_excel_load(message: Message, state: FSMContext):
    data = await state.get_data()
    df, err = await download_excel(message)
    if err:
        await message.answer(err)
        return

    # Ustun nomlarini bir xil (kichik harf) ga keltiramiz
    df.columns = [str(c).strip().lower() for c in df.columns]
    if not {"sana", "student_id"}.issubset(set(df.columns)):
        await message.answer(
            "❌ Ustunlar kerak: sana, student_id "
            "(group, ism, familya, status — ixtiyoriy)."
        )
        await state.clear()
        return

    has_status = "status" in df.columns

    async with async_session() as session:
        valid_ids = set((await session.scalars(
            select(Student.id).where(Student.group_id == data["group_id"])
        )).all())

        added, skipped = 0, 0
        for _, row in df.iterrows():
            sid = safe_int(row.get("student_id"))
            if sid is None or sid not in valid_ids:
                skipped += 1
                continue

            raw_day = str(row.get("sana", "")).strip()[:10]
            try:
                day = datetime.strptime(raw_day, "%Y-%m-%d").date()
            except ValueError:
                skipped += 1
                continue

            present = 1
            if has_status:
                st = safe_int(row.get("status"))
                present = 1 if (st is None or st == 1) else 0

            existing = await session.scalar(
                select(Attendance).where(
                    Attendance.student_id == sid, Attendance.day == day)
            )
            if existing:
                existing.present = present
            else:
                session.add(Attendance(student_id=sid, day=day, present=present))
            added += 1
        await session.commit()

    await message.answer(
        f"✅ Davomat yuklandi: {added} ta\n⚠️ O'tkazib yuborildi: {skipped} ta",
        reply_markup=admin_menu(),
    )
    await state.clear()


@router.message(AttendanceFSM.file)
async def att_excel_invalid(message: Message):
    await message.answer("❌ Iltimos, .xlsx faylni yuboring.")
