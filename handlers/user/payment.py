from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from config import ADMINS
from states.states import PaymentFSM, ConfirmFSM
from database.engine import async_session
from database.models import Student, PaymentRequest
from keyboards.inline import students_select_kb, pay_now_kb, payment_decision_kb
from keyboards.buttons import BTN_PAY
from utils.helpers import group_label, safe_delete, safe_edit_caption
from utils.cards import cards_text_db

router = Router()


@router.message(F.text == BTN_PAY)
async def pay_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("To'lov qilinadigan o'quvchining ism/familiyasini kiriting:")
    await state.set_state(PaymentFSM.search)


@router.message(PaymentFSM.search)
async def pay_search(message: Message, state: FSMContext):
    q = message.text.strip()
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group)).where(or_(
                Student.name.ilike(f"%{q}%"), Student.last_name.ilike(f"%{q}%")))
        )).all()
    if not students:
        await message.answer("❌ Topilmadi. Qayta urinib ko'ring:")
        return
    if len(students) == 1:
        await state.update_data(pay_student_id=students[0].id)
        await _show(message, students[0])
        await state.set_state(PaymentFSM.select)
        return
    await message.answer(f"🔍 {len(students)} ta topildi. Tanlang:",
                         reply_markup=students_select_kb(students, "paypick"))
    await state.set_state(PaymentFSM.select)


@router.callback_query(PaymentFSM.select, F.data.startswith("paypick:"))
async def pay_pick(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[1])
    async with async_session() as session:
        s = await session.scalar(
            select(Student).options(selectinload(Student.group)).where(Student.id == sid))
    await safe_delete(call.message)
    if s:
        await state.update_data(pay_student_id=s.id)
        await _show(call.message, s)
    await call.answer()


async def _show(message: Message, s: Student):
    debt = "\n⚠️ <b>Sizda qarz mavjud.</b> Iltimos, to'lovni amalga oshiring." if s.balance < 0 else ""
    await message.answer(f"👤 <b>{s.name} {s.last_name}</b>\n👥 Guruh: {group_label(s)}{debt}",
                         reply_markup=pay_now_kb(s.id))


@router.callback_query(PaymentFSM.select, F.data.startswith("paynow:"))
async def pay_now(call: CallbackQuery, state: FSMContext):
    # Eski tugmani o'chiramiz (qayta bosilmasin)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.update_data(pay_student_id=int(call.data.split(":")[1]))
    text = await cards_text_db()
    await call.message.answer(text +
        "\n💸 Yuqoridagi kartaga to'lang, so'ng <b>chek (rasm)</b> yuboring:")
    await state.set_state(PaymentFSM.check)
    await call.answer()


@router.message(PaymentFSM.check, F.photo)
async def pay_check(message: Message, state: FSMContext):
    data = await state.get_data()
    sid = data.get("pay_student_id")
    if not sid:
        await message.answer("❌ Sessiya tugadi. «💳 To'lov qilish» tugmasidan qayta boshlang.")
        await state.clear()
        return
    async with async_session() as session:
        s = await session.scalar(
            select(Student).options(selectinload(Student.group))
            .where(Student.id == sid))
        if not s:
            await message.answer("❌ O'quvchi topilmadi. Qaytadan boshlang.")
            await state.clear()
            return
        req = PaymentRequest(student_id=s.id, user_id=message.from_user.id, status="pending")
        session.add(req)
        await session.commit()
        req_id = req.id
        cap = (f"💳 <b>Yangi to'lov cheki</b>\n👤 {s.name} {s.last_name}\n"
               f"👥 {group_label(s)}\n💰 Balans: {s.balance:,.0f} so'm\n"
               f"🆔 TG: <code>{message.from_user.id}</code>")

    kb = payment_decision_kb(req_id)
    sent_ok = False
    for admin_id in ADMINS:
        try:
            await message.bot.send_photo(admin_id, photo=message.photo[-1].file_id,
                                         caption=cap, reply_markup=kb)
            sent_ok = True
        except Exception:
            pass

    if sent_ok:
        await message.answer("✅ Chek adminlarga yuborildi. Tasdiqlashni kuting.")
    else:
        await message.answer("⚠️ Chek yuborilmadi (admin topilmadi). Keyinroq urinib ko'ring.")
    await state.clear()


@router.message(PaymentFSM.check)
async def pay_invalid(message: Message):
    await message.answer("❌ Iltimos, chekni <b>rasm</b> qilib yuboring.")


@router.callback_query(F.data.startswith("confirm:"))
async def confirm(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    req_id = int(call.data.split(":")[1])
    async with async_session() as session:
        req = await session.get(PaymentRequest, req_id)
        if not req or req.status != "pending":
            await call.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
            return
    await state.set_state(ConfirmFSM.amount)
    await state.update_data(req_id=req_id)
    await call.message.answer("To'lov summasini kiriting (balansga qo'shiladi):")
    await call.answer()


@router.message(ConfirmFSM.amount, F.from_user.id.in_(ADMINS))
async def confirm_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(" ", "").replace(",", ""))
    except (ValueError, AttributeError):
        await message.answer("❌ Faqat raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        req = await session.get(PaymentRequest, data["req_id"])
        if not req or req.status != "pending":
            await message.answer("⚠️ Bu to'lov allaqachon tasdiqlangan.")
            await state.clear()
            return
        student = await session.get(Student, req.student_id)
        student.balance += amount
        req.status = "confirmed"
        await session.commit()
        nb, fn, uid = student.balance, f"{student.name} {student.last_name}", req.user_id

    if nb < 0:
        status_line = "⚠️ Sizda hali qarz mavjud. Iltimos, to'lovni davom ettiring."
    else:
        status_line = "✅ Qarzingiz yo'q. Rahmat! 🎉"

    try:
        await message.bot.send_message(
            uid,
            f"✅ <b>To'lovingiz tasdiqlandi:</b> {amount:,.0f} so'm\n"
            f"👤 {fn}\n━━━━━━━━━━━━━━\n{status_line}"
        )
    except Exception:
        pass

    await message.answer(f"✅ Tasdiqlandi. {fn} — balans: {nb:,.0f} so'm")
    await state.clear()


@router.callback_query(F.data.startswith("reject:"))
async def reject(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    req_id = int(call.data.split(":")[1])
    async with async_session() as session:
        req = await session.get(PaymentRequest, req_id)
        if not req or req.status != "pending":
            await call.answer("⚠️ Allaqachon ko'rib chiqilgan.", show_alert=True)
            return
        req.status = "rejected"
        await session.commit()
        uid = req.user_id
    try:
        await call.bot.send_message(uid, "❌ To'lovingiz rad etildi. Admin bilan bog'laning.")
    except Exception:
        pass
    await safe_edit_caption(call, "\n\n❌ <b>RAD ETILDI</b>")
    await call.answer("Rad etildi")
