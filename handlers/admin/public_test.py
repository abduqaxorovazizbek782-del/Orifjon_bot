from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config import ADMINS, GROUP_IDS
from states.states import PublicTestFSM
from database.engine import async_session
from database.models import TestArchive, BotUser
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_PUBLIC_TEST
from utils.broadcast import broadcast

router = Router()


@router.message(F.text == BTN_PUBLIC_TEST, F.from_user.id.in_(ADMINS))
async def pt_start(message: Message, state: FSMContext):
    await message.answer("🧾 Test natijasi faylini yuboring (Excel/PDF/rasm):")
    await state.set_state(PublicTestFSM.file)


@router.message(PublicTestFSM.file, F.document)
async def pt_doc(message: Message, state: FSMContext):
    await state.update_data(file_id=message.document.file_id, file_type="document",
                            file_name=message.document.file_name)
    await message.answer("✍️ Izoh yozing (masalan: Bugungi DTM test natijalari):")
    await state.set_state(PublicTestFSM.caption)


@router.message(PublicTestFSM.file, F.photo)
async def pt_photo(message: Message, state: FSMContext):
    await state.update_data(file_id=message.photo[-1].file_id, file_type="photo", file_name=None)
    await message.answer("✍️ Izoh yozing:")
    await state.set_state(PublicTestFSM.caption)


@router.message(PublicTestFSM.file)
async def pt_invalid(message: Message):
    await message.answer("❌ Iltimos, fayl yoki rasm yuboring.")


@router.message(PublicTestFSM.caption)
async def pt_caption(message: Message, state: FSMContext):
    caption = message.text.strip()
    data = await state.get_data()
    # Faqat arxivga - o'quvchilar bazasiga ta'sir QILMAYDI
    async with async_session() as session:
        session.add(TestArchive(file_id=data["file_id"], file_type=data["file_type"],
                                file_name=data.get("file_name"), caption=caption))
        await session.commit()
        users = (await session.scalars(select(BotUser.tg_id))).all()

    nice = f"🧾 <b>Test natijasi</b>\n━━━━━━━━━━━━━━\n{caption}"
    kind = data["file_type"]
    fid = data["file_id"]

    await message.answer("📤 Yuborish boshlandi, kuting...")

    sent, failed = await broadcast(message.bot, users, nice, kind=kind, file_id=fid)
    gsent, gfailed = await broadcast(message.bot, GROUP_IDS, nice, kind=kind, file_id=fid)

    await message.answer(
        f"✅ Test natijasi tarqatildi va arxivga saqlandi.\n"
        f"👤 Userlar: {sent} yuborildi, {failed} xato\n"
        f"👥 Guruhlar: {gsent} yuborildi, {gfailed} xato",
        reply_markup=admin_menu()
    )
    await state.clear()
