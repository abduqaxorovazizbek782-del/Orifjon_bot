from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config import ADMINS
from states.states import ExcelFSM
from database.engine import async_session
from database.models import Student, Group
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_EXCEL_UPLOAD
from utils.helpers import download_excel, safe_int

router = Router()


@router.message(F.text == BTN_EXCEL_UPLOAD, F.from_user.id.in_(ADMINS))
async def ask_excel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📥 .xlsx faylni yuboring.\n"
        "Ustunlar: <code>name, last_name, tel, group_id</code>\n\n"
        "ℹ️ <code>group_id</code> ni to'g'ri yozing. Guruh ID larini "
        "«🆔 O'quvchi va Guruh ID lari (Excel)» dan olishingiz mumkin."
    )
    await state.set_state(ExcelFSM.file)


@router.message(ExcelFSM.file, F.document)
async def load_excel(message: Message, state: FSMContext):
    df, err = await download_excel(message)
    if err:
        await message.answer(err)
        return

    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"name", "last_name", "tel", "group_id"}
    if not required.issubset(set(df.columns)):
        await message.answer(f"❌ Ustunlar yetishmaydi. Kerak: {', '.join(required)}")
        await state.clear()
        return

    added, skipped = 0, 0
    bad_rows = []

    async with async_session() as session:
        valid_group_ids = set((await session.scalars(select(Group.id))).all())

        for idx, row in enumerate(df.itertuples(index=False), start=2):
            row_dict = row._asdict() if hasattr(row, "_asdict") else dict(zip(df.columns, row))

            name = str(row_dict.get("name", "")).strip()
            last = str(row_dict.get("last_name", "")).strip()
            gid = safe_int(row_dict.get("group_id"))

            who = f"{name} {last}".strip() or f"{idx}-qator"

            if not name or not last:
                skipped += 1
                bad_rows.append(f"{idx}-qator: ism yoki familiya to'ldirilmagan")
                continue

            if gid is None:
                skipped += 1
                bad_rows.append(f"❌ {who}: guruh ID bo'sh yoki noto'g'ri")
                continue

            if gid not in valid_group_ids:
                skipped += 1
                bad_rows.append(f"❌ {who}: guruh ID {gid} mavjud emas")
                continue

            tel = str(row_dict.get("tel", "")).strip()
            student = Student(name=name, last_name=last, tel=tel,
                              group_id=gid, balance=0.0)
            session.add(student)
            try:
                await session.flush()
                added += 1
            except Exception:
                await session.rollback()
                skipped += 1
                bad_rows.append(f"❌ {who}: bazaga yozib bo'lmadi")
                valid_group_ids = set((await session.scalars(select(Group.id))).all())

        await session.commit()

    text = (f"✅ Qo'shildi: <b>{added}</b> ta o'quvchi\n"
            f"⚠️ O'tkazib yuborildi: <b>{skipped}</b> ta")
    if bad_rows:
        shown = bad_rows[:20]
        text += "\n\n<b>⚠️ Xatolik bor o'quvchilar:</b>\n" + "\n".join(shown)
        if len(bad_rows) > 20:
            text += f"\n... va yana {len(bad_rows) - 20} ta"

    await message.answer(text, reply_markup=admin_menu())
    await state.clear()


@router.message(ExcelFSM.file)
async def excel_invalid(message: Message):
    await message.answer("❌ Iltimos, .xlsx faylni yuboring.")
