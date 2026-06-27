from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMINS
from states.states import GroupFSM
from database.engine import async_session
from database.models import Group
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_NEW_GROUP

router = Router()


@router.message(F.text == BTN_NEW_GROUP, F.from_user.id.in_(ADMINS))
async def new_group(message: Message, state: FSMContext):
    await message.answer("Guruh nomini kiriting:")
    await state.set_state(GroupFSM.name)


@router.message(GroupFSM.name)
async def group_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("O'quv yilini kiriting (masalan: 2025):")
    await state.set_state(GroupFSM.year)


@router.message(GroupFSM.year)
async def group_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
        if not (2000 <= year <= 2100):
            raise ValueError
    except ValueError:
        await message.answer("❌ Yil noto'g'ri. Masalan: 2025")
        return
    await state.update_data(year=year)
    await message.answer("Oylik narxini kiriting (faqat raqam):")
    await state.set_state(GroupFSM.price)


@router.message(GroupFSM.price)
async def group_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Narx noto'g'ri. Faqat raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        session.add(Group(name=data["name"], year=data["year"], monthly_price=price))
        await session.commit()
    await message.answer(
        f"✅ Guruh yaratildi:\n📁 <b>{data['name']}</b>\n"
        f"🗓 Yil: <b>{data['year']}</b>\n💰 Oylik: {price:,.0f} so'm",
        reply_markup=admin_menu()
    )
    await state.clear()
