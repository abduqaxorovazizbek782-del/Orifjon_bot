from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import ADMINS
from database.engine import async_session
from database.models import Student
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_IDS_EXCEL
from utils.helpers import make_excel

router = Router()


@router.message(F.text == BTN_IDS_EXCEL, F.from_user.id.in_(ADMINS))
async def ids_excel(message: Message):
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
            .order_by(Student.group_id, Student.name)
        )).all()

    if not students:
        await message.answer("❌ Hozircha o'quvchilar yo'q.", reply_markup=admin_menu())
        return

    rows = []
    for s in students:
        g = s.group
        rows.append({
            "student_id": s.id,
            "Ism": s.name,
            "Familiya": s.last_name,
            "Telefon": s.tel or "",
            "group_id": g.id if g else "",
            "Guruh": g.name if g else "",
            "Guruh yili": g.year if g else "",
        })

    buffer = make_excel(rows, sheet_name="ID lar")
    file = BufferedInputFile(buffer.read(), filename="oquvchi_va_guruh_idlari.xlsx")
    await message.answer_document(
        file,
        caption=(
            "🆔 <b>O'quvchi va Guruh ID lari</b>\n"
            f"👥 Jami: {len(students)} ta o'quvchi\n\n"
            "Bu fayldagi <code>student_id</code> va <code>group_id</code> ni "
            "test/davomat yuklashda ishlatishingiz mumkin."
        ),
        reply_markup=admin_menu(),
    )
