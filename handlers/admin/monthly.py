from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import MonthlyFSM
from database.engine import async_session
from database.models import Student, MonthlyBilling
from keyboards.reply import admin_menu
from keyboards.inline import monthly_confirm_kb, monthly_final_kb
from keyboards.buttons import BTN_MONTHLY

router = Router()


def _current_period() -> str:
    return datetime.now().strftime("%Y-%m")


async def _period_rows(session, period: str):
    return (await session.scalars(
        select(MonthlyBilling).where(MonthlyBilling.period == period)
    )).all()


def _dates_text(rows) -> str:
    dates = [r.created_at.strftime("%Y-%m-%d %H:%M") for r in rows]
    return "\n".join(f"   • {d}" for d in dates)


async def run_monthly_billing(admin_id: int | None = None) -> tuple[int, float]:
    period = _current_period()
    count, total = 0, 0.0
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
        )).all()
        for s in students:
            if not s.group:
                continue
            s.balance -= s.group.monthly_price
            total += s.group.monthly_price
            count += 1
        session.add(MonthlyBilling(
            period=period, students_count=count,
            total_amount=total, created_by=admin_id,
        ))
        await session.commit()
    return count, total


@router.message(F.text == BTN_MONTHLY, F.from_user.id.in_(ADMINS))
async def monthly_start(message: Message, state: FSMContext):
    period = _current_period()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
        )).all()
        rows = await _period_rows(session, period)

    count = sum(1 for s in students if s.group)
    total = sum(s.group.monthly_price for s in students if s.group)
    times = len(rows)

    warn = ""
    if times > 0:
        period_total = sum(r.total_amount for r in rows)
        warn = (
            f"\n⚠️ <b>DIQQAT:</b> Bu oy ({period}) allaqachon "
            f"<b>{times} marta</b> qilingan!\n"
            f"📅 Qilingan sanalar:\n{_dates_text(rows)}\n"
            f"💸 Shu oyda jami yozilgan: {period_total:,.0f} so'm\n"
        )

    await message.answer(
        "⚠️ <b>Oylik hisob-kitob</b>\n"
        "━━━━━━━━━━━━━━\n"
        "Bu amal <b>BARCHA o'quvchilarga</b> oylik to'lovni yozadi.\n"
        f"{warn}\n"
        f"👥 Ta'sir qiladi: <b>{count}</b> o'quvchi\n"
        f"💸 Jami yoziladigan: <b>{total:,.0f}</b> so'm\n\n"
        "Davom etamizmi?",
        reply_markup=monthly_confirm_kb(),
    )
    await state.set_state(MonthlyFSM.confirm)


@router.callback_query(MonthlyFSM.confirm, F.data == "monthly_yes",
                       F.from_user.id.in_(ADMINS))
async def monthly_ask_again(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.edit_text(
            "❗️ <b>Oxirgi tasdiq</b>\n"
            "━━━━━━━━━━━━━━\n"
            "Rostdan ham barcha o'quvchilarga oylik to'lov yozilsinmi?\n"
            "Bu amalni ortga qaytarib bo'lmaydi.",
            reply_markup=monthly_final_kb(),
        )
    except Exception:
        await call.message.answer("❗️ Rostdan ham yozilsinmi?",
                                  reply_markup=monthly_final_kb())
    await call.answer()


@router.callback_query(MonthlyFSM.confirm, F.data == "monthly_final_yes",
                       F.from_user.id.in_(ADMINS))
async def monthly_final_yes(call: CallbackQuery, state: FSMContext):
    count, total = await run_monthly_billing(admin_id=call.from_user.id)
    period = _current_period()
    async with async_session() as session:
        rows = await _period_rows(session, period)
    times = len(rows)
    period_total = sum(r.total_amount for r in rows)
    try:
        await call.message.edit_text(
            "✅ <b>Oylik hisob-kitob bajarildi.</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"👥 O'quvchilar: {count}\n"
            f"💸 Yozildi: {total:,.0f} so'm\n"
            f"📅 Bu oy ({period}) jami: {times} marta, {period_total:,.0f} so'm"
        )
    except Exception:
        pass
    await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
    await call.answer()


@router.callback_query(MonthlyFSM.confirm, F.data.in_(["monthly_no", "monthly_final_no"]),
                       F.from_user.id.in_(ADMINS))
async def monthly_no(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.edit_text("🚫 Bekor qilindi. Hech narsa o'zgarmadi.")
    except Exception:
        pass
    await call.message.answer("Bosh menyu:", reply_markup=admin_menu())
    await state.clear()
    await call.answer()
