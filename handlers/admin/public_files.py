from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config import ADMINS, GROUP_IDS
from states.states import PublicUploadFSM
from database.engine import async_session
from database.models import UploadedFile, BotUser
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_PUBLIC_UPLOAD
from utils.broadcast import broadcast

router = Router()


@router.message(F.text == BTN_PUBLIC_UPLOAD, F.from_user.id.in_(ADMINS))
async def pf_start(message: Message, state: FSMContext):
    await message.answer("📢 Tarqatiladigan faylni yuboring (Excel/PDF/rasm):")
    await state.set_state(PublicUploadFSM.file)


@router.message(PublicUploadFSM.file, F.document)
async def pf_doc(message: Message, state: FSMContext):
    await state.update_data(file_id=message.document.file_id, file_type="document",
                            file_name=message.document.file_name)
    await message.answer("✍️ Izoh yozing:")
    await state.set_state(PublicUploadFSM.caption)


@router.message(PublicUploadFSM.file, F.photo)
async def pf_photo(message: Message, state: FSMContext):
    await state.update_data(file_id=message.photo[-1].file_id, file_type="photo", file_name=None)
    await message.answer("✍️ Izoh yozing:")
    await state.set_state(PublicUploadFSM.caption)


@router.message(PublicUploadFSM.file)
async def pf_invalid(message: Message):
    await message.answer("❌ Iltimos, fayl yoki rasm yuboring.")


@router.message(PublicUploadFSM.caption)
async def pf_caption(message: Message, state: FSMContext):
    caption = message.text.strip()
    data = await state.get_data()
    async with async_session() as session:
        session.add(UploadedFile(file_id=data["file_id"], file_type=data["file_type"],
                                 file_name=data.get("file_name"), caption=caption))
        await session.commit()
        users = (await session.scalars(select(BotUser.tg_id))).all()

    nice = f"📢 <b>Yangi e'lon / fayl</b>\n━━━━━━━━━━━━━━\n{caption}"
    kind = data["file_type"]   # "photo" | "document"
    fid = data["file_id"]

    await message.answer("📤 Yuborish boshlandi, kuting...")

    sent, failed = await broadcast(message.bot, users, nice, kind=kind, file_id=fid)
    gsent, gfailed = await broadcast(message.bot, GROUP_IDS, nice, kind=kind, file_id=fid)

    await message.answer(
        f"✅ Tarqatildi.\n"
        f"👤 Userlar: {sent} yuborildi, {failed} xato\n"
        f"👥 Guruhlar: {gsent} yuborildi, {gfailed} xato",
        reply_markup=admin_menu()
    )
    await state.clear()
