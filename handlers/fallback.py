from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from config import ADMINS
from keyboards.reply import admin_menu, user_menu

router = Router()


@router.message(StateFilter(None))
async def fallback(message: Message, state: FSMContext):
    is_admin = message.from_user.id in ADMINS
    menu = admin_menu() if is_admin else user_menu()

    text = (
        "🤖 <b>Tushunmadim 😊</b>\n"
        "━━━━━━━━━━━━━━\n"
        "Iltimos, matn yozish o'rniga quyidagi\n"
        "<b>menyu tugmalaridan</b> birini tanlang 👇"
    )
    await message.answer(text, reply_markup=menu)
