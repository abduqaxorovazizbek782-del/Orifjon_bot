from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from database.engine import async_session
from database.models import Student
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_DEBTORS_EXCEL
from utils.helpers import make_excel

router = Router()


@router.message(F.text == BTN_DEBTORS_EXCEL, F.from_user.id.in_(ADMINS))
async def debtors_excel(message: Message):
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
        )).all()

    debtors = [s for s in students if s.balance < 0]
    if not debtors:
        await message.answer("✅ Hozircha qarzdorlar yo'q.", reply_markup=admin_menu())
        return

    rows = []
    for s in debtors:
        g = s.group
        rows.append({
            "ID": s.id,
            "Ism": s.name,
            "Familiya": s.last_name,
            "Telefon": s.tel or "",
            "Guruh": g.name if g else "",
            "Guruh ID": g.id if g else "",
            "Guruh yili": g.year if g else "",
            "Qarz (so'm)": abs(s.balance),
        })

    buffer = make_excel(rows, sheet_name="Qarzdorlar")
    file = BufferedInputFile(buffer.read(), filename="qarzdorlar.xlsx")
    await message.answer_document(
        file,
        caption=f"📑 <b>Qarzdorlar ro'yxati</b>\n👥 Jami: {len(debtors)} ta",
        reply_markup=admin_menu(),
    )
