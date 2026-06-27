from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from aiogram.types import FSInputFile

from config import ADMINS
from database.engine import async_session
from database.models import Student, MonthlyBilling
from keyboards.inline import monthly_confirm_kb
from utils.backup import make_backup


async def _ask_monthly_confirmation(bot):
    period = datetime.now().strftime("%Y-%m")
    async with async_session() as session:
        students = (await session.scalars(
            select(Student).options(selectinload(Student.group))
        )).all()
        rows = (await session.scalars(
            select(MonthlyBilling).where(MonthlyBilling.period == period)
        )).all()

    count = sum(1 for s in students if s.group)
    total = sum(s.group.monthly_price for s in students if s.group)
    times = len(rows)

    warn = f"\n⚠️ Bu oy allaqachon {times} marta qilingan!\n" if times > 0 else ""

    text = (
        "🗓 <b>Oylik hisob-kitob vaqti keldi!</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"📅 Oy: <b>{period}</b>\n"
        f"👥 O'quvchilar: <b>{count}</b>\n"
        f"💸 Yoziladigan: <b>{total:,.0f}</b> so'm\n"
        f"{warn}\n"
        "Hammaga oylik to'lov yozilsinmi?"
    )
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text, reply_markup=monthly_confirm_kb())
        except Exception:
            pass


async def _daily_backup(bot):
    """Backup oladi va birinchi adminga Telegram orqali yuboradi."""
    path = make_backup()
    if not path:
        return
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for admin_id in ADMINS:
        try:
            await bot.send_document(
                admin_id,
                FSInputFile(path),
                caption=f"💾 <b>Kunlik backup</b>\n🗓 {stamp}",
            )
        except Exception:
            pass


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    scheduler.add_job(
        _ask_monthly_confirmation,
        trigger=CronTrigger(day=1, hour=9, minute=0),
        id="monthly_ask",
        replace_existing=True,
        kwargs={"bot": bot},
    )

    scheduler.add_job(
        _daily_backup,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_backup",
        replace_existing=True,
        kwargs={"bot": bot},
    )

    return scheduler
