from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config import ADMINS
from database.engine import async_session
from database.models import BotUser
from keyboards.reply import admin_menu, user_menu

router = Router()


WELCOME_ADMIN = (
    "👋 <b>Admin panelga xush kelibsiz!</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Quyidagi menyu tugmalari orqali boshqarasiz:\n\n"
    "📁 <b>Guruh va o'quvchilar</b> — guruh yaratish, o'quvchi qo'shish, "
    "Exceldan yuklash, ro'yxatni ko'rish.\n"
    "💸 <b>Moliya</b> — qarz yozish, oylik hisob-kitob, qarzdorlar (Excel).\n"
    "🗓 <b>Davomat</b> — guruh bo'yicha davomat olish.\n"
    "📊 <b>Testlar</b> — test natijalarini yuklash.\n"
    "📢 <b>E'lonlar</b> — ommaviy fayl va test natijalarini tarqatish.\n\n"
    "ℹ️ <code>/warning</code> — barcha user va guruhlarga e'lon yuborish.\n"
    "ℹ️ Murojaatlarga <b>reply</b> qilib javob berasiz."
)


WELCOME_USER = (
    "👋 <b>Assalomu alaykum!</b>\n"
    "O'quv markazi rasmiy botiga xush kelibsiz 🎓\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Bu bot orqali siz quyidagilarni qila olasiz:\n\n"
    "📉 <b>To'lov va Qarzni tekshirish</b>\n"
    "   Ism yoki familiyani yozib, holatni ko'ring.\n\n"
    "💳 <b>To'lov qilish</b>\n"
    "   O'quvchini tanlab, kartaga to'lang va chek (rasm) yuboring. "
    "Admin tasdiqlaydi.\n\n"
    "🏆 <b>O'quvchi reytingi</b>\n"
    "   O'quvchining o'rtacha test natijasi va davomatini ko'ring.\n\n"
    "📅 <b>Testlar tarixi</b>\n"
    "   Barcha test natijalarini ko'ring.\n\n"
    "📂 <b>Fayllar</b> va 📊 <b>Test natijalari</b>\n"
    "   Markaz yuklagan fayl va natijalarni oling.\n\n"
    "✉️ <b>Admin bilan bog'lanish</b>\n"
    "   Savol yoki muammoingizni to'g'ridan-to'g'ri adminga yozing.\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "👇 Boshlash uchun pastdagi menyu tugmasini tanlang."
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    try:
        async with async_session() as session:
            exists = await session.scalar(
                select(BotUser).where(BotUser.tg_id == message.from_user.id)
            )
            if not exists:
                session.add(BotUser(
                    tg_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    username=message.from_user.username,
                ))
                await session.commit()
    except Exception:
        pass

    if message.from_user.id in ADMINS:
        await message.answer(WELCOME_ADMIN, reply_markup=admin_menu())
    else:
        await message.answer(WELCOME_USER, reply_markup=user_menu())
