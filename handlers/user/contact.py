from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext

from config import ADMINS
from states.states import ContactFSM
from keyboards.reply import user_menu
from keyboards.buttons import BTN_CONTACT_ADMIN

router = Router()

# Adminga yuboriladigan xabardagi belgi (reply orqali userni topish uchun)
TAG = "🆔 User:"

BTN_SKIP = "⏭ O'tkazib yuborish"
BTN_CANCEL = "❌ Bekor qilish"


def _extra_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SKIP)], [KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


# ───────────── USER TOMONI ─────────────

@router.message(F.text == BTN_CONTACT_ADMIN)
async def contact_start(message: Message, state: FSMContext):
    await message.answer(
        "✍️ Adminga yubormoqchi bo'lgan xabaringizni <b>matn</b> ko'rinishida yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(ContactFSM.text)


@router.message(ContactFSM.text, F.text)
async def contact_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    await message.answer(
        "📎 Xabaringizga <b>rasm yoki fayl</b> ham qo'shasizmi?\n"
        "Qo'shmoqchi bo'lsangiz hoziroq yuboring.\n"
        "Aks holda «O'tkazib yuborish» tugmasini bosing.",
        reply_markup=_extra_kb(),
    )
    await state.set_state(ContactFSM.ask_extra)


@router.message(ContactFSM.text)
async def contact_text_invalid(message: Message):
    await message.answer("❌ Iltimos, avval xabaringizni matn ko'rinishida yozing.")


# 2-qadam: "O'tkazib yuborish" bosildi -> faqat matn ketadi
@router.message(ContactFSM.ask_extra, F.text == BTN_SKIP)
async def contact_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    await _send_to_admins(message, text=data.get("text", ""), media=None)
    await message.answer("✅ Xabaringiz adminga yuborildi.", reply_markup=user_menu())
    await state.clear()


# Bekor qilish (har qadamda)
@router.message(ContactFSM.ask_extra, F.text == BTN_CANCEL)
async def contact_cancel(message: Message, state: FSMContext):
    await message.answer("🚫 Bekor qilindi.", reply_markup=user_menu())
    await state.clear()


# 2-qadam: rasm yoki fayl yuborildi -> matn + media ketadi
@router.message(ContactFSM.ask_extra, F.photo | F.document)
async def contact_extra(message: Message, state: FSMContext):
    data = await state.get_data()
    await _send_to_admins(message, text=data.get("text", ""), media=message)
    await message.answer("✅ Xabaringiz va fayl adminga yuborildi.", reply_markup=user_menu())
    await state.clear()


@router.message(ContactFSM.ask_extra)
async def contact_extra_invalid(message: Message):
    await message.answer(
        "❌ Rasm/fayl yuboring yoki «O'tkazib yuborish» tugmasini bosing.",
        reply_markup=_extra_kb(),
    )


async def _send_to_admins(message: Message, text: str, media: Message | None):
    """Adminlarga sarlavha + matn, kerak bo'lsa media yuboradi."""
    u = message.from_user
    uname = f"@{u.username}" if u.username else "—"
    header = (
        f"📨 <b>Yangi murojaat</b>\n"
        f"👤 {u.full_name} ({uname})\n"
        f"{TAG} <code>{u.id}</code>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💬 {text}"
    )
    for admin_id in ADMINS:
        try:
            await message.bot.send_message(admin_id, header)
            if media is not None:
                await media.copy_to(admin_id)
        except Exception:
            pass


# ───────────── ADMIN TOMONI (REPLY) ─────────────
# DIQQAT: faqat state YO'Q bo'lganda va reply matnida TAG bo'lganda ishlaydi.
# Bu admin boshqa FSM oqimida (test, warning, confirm) bo'lsa aralashmaydi.

@router.message(
    F.from_user.id.in_(ADMINS),
    F.reply_to_message,
    F.reply_to_message.text.contains(TAG),
)
async def admin_reply(message: Message):
    text = message.reply_to_message.text or ""
    try:
        after = text.split(TAG, 1)[1].strip()
        uid = int(after.split()[0])
    except (IndexError, ValueError):
        await message.answer("⚠️ User ID aniqlanmadi.")
        return

    try:
        await message.bot.send_message(uid, "📬 <b>Admin javobi:</b>\n━━━━━━━━━━━━━━")
        await message.copy_to(uid)
        await message.answer("✅ Javob userga yuborildi.")
    except Exception:
        await message.answer("❌ Userga yuborib bo'lmadi (bot bloklangan bo'lishi mumkin).")
