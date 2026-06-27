import html

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete

from config import ADMINS
from states.states import CardFSM
from database.engine import async_session
from database.models import PaymentCard
from keyboards.reply import admin_menu
from keyboards.inline import cards_manage_kb, card_del_confirm_kb
from keyboards.buttons import BTN_PAYMENT_CARDS
from utils.cards import get_cards, MAX_CARDS
from utils.helpers import safe_delete

router = Router()


def _esc(text) -> str:
    """HTML maxsus belgilarini xavfsiz qiladi (<, >, &)."""
    return html.escape(str(text)) if text else ""


async def _render_list(target: Message):
    cards = await get_cards()
    if not cards:
        head = ("💳 <b>To'lov kartalari</b>\n\nHozircha karta yo'q.\n"
                "(Standart karta ko'rsatilmoqda.)")
    else:
        lines = ["💳 <b>To'lov kartalari</b>\n"]
        for i, c in enumerate(cards, 1):
            tel = f"\n📞 {_esc(c.tel)}" if c.tel else ""
            lines.append(f"{i}. 🧑 {_esc(c.name)}\n💳 <code>{_esc(c.card)}</code>{tel}\n")
        head = "\n".join(lines)
    await target.answer(head, reply_markup=cards_manage_kb(cards))


@router.message(F.text == BTN_PAYMENT_CARDS, F.from_user.id.in_(ADMINS))
async def cards_menu(message: Message, state: FSMContext):
    await state.clear()
    await _render_list(message)


# ───── O'CHIRISH ─────

@router.callback_query(F.data.startswith("card_del:"))
async def card_del_ask(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    cid = int(call.data.split(":")[1])
    async with async_session() as session:
        c = await session.get(PaymentCard, cid)
    if not c:
        await call.answer("Topilmadi.", show_alert=True)
        return
    try:
        await call.message.edit_text(
            f"⚠️ <b>{_esc(c.name)}</b>\n💳 <code>{_esc(c.card)}</code>\n\n"
            "Ushbu kartani aniq o'chirasizmi?",
            reply_markup=card_del_confirm_kb(cid)
        )
    except Exception:
        await call.message.answer(
            f"⚠️ <b>{_esc(c.name)}</b> kartasini aniq o'chirasizmi?",
            reply_markup=card_del_confirm_kb(cid)
        )
    await call.answer()


@router.callback_query(F.data.startswith("card_delok:"))
async def card_del_ok(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    cid = int(call.data.split(":")[1])
    async with async_session() as session:
        await session.execute(delete(PaymentCard).where(PaymentCard.id == cid))
        await session.commit()
    await safe_delete(call.message)
    await call.message.answer("❌ Karta o'chirildi.")
    await _render_list(call.message)
    await call.answer("O'chirildi")


@router.callback_query(F.data.startswith("card_delno:"))
async def card_del_no(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("✅ Bekor qilindi.")
    await _render_list(call.message)
    await call.answer()


# ───── QO'SHISH ─────

@router.callback_query(F.data == "card_add")
async def card_add_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMINS:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    cards = await get_cards()
    if len(cards) >= MAX_CARDS:
        await call.answer(f"Maksimum {MAX_CARDS} ta karta!", show_alert=True)
        return
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer("🧑 Karta egasining ism-familiyasini kiriting:")
    await state.set_state(CardFSM.name)
    await call.answer()


@router.message(CardFSM.name, F.from_user.id.in_(ADMINS))
async def card_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("💳 Karta raqamini kiriting:")
    await state.set_state(CardFSM.card)


@router.message(CardFSM.card, F.from_user.id.in_(ADMINS))
async def card_number(message: Message, state: FSMContext):
    await state.update_data(card=message.text.strip())
    await message.answer("📞 Telefon raqamini kiriting (yo'q bo'lsa: -):")
    await state.set_state(CardFSM.tel)


@router.message(CardFSM.tel, F.from_user.id.in_(ADMINS))
async def card_tel(message: Message, state: FSMContext):
    tel = message.text.strip()
    if tel == "-":
        tel = None
    data = await state.get_data()
    async with async_session() as session:
        count = len((await session.scalars(select(PaymentCard))).all())
        if count >= MAX_CARDS:
            await message.answer(f"❌ Maksimum {MAX_CARDS} ta karta.",
                                 reply_markup=admin_menu())
            await state.clear()
            return
        session.add(PaymentCard(name=data["name"], card=data["card"], tel=tel))
        await session.commit()
    await message.answer("✅ Karta qo'shildi.", reply_markup=admin_menu())
    await state.clear()
    await _render_list(message)
