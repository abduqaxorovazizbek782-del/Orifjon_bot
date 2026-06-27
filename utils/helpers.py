import io
import math
import pandas as pd


def group_label(student) -> str:
    if student.group:
        return f"{student.group.name} [{student.group.year}]"
    return "—"


async def safe_delete(message):
    try:
        await message.delete()
    except Exception:
        pass


async def safe_edit_caption(call, extra: str):
    try:
        if call.message.caption is not None:
            await call.message.edit_caption(caption=call.message.caption + extra)
        elif call.message.text is not None:
            await call.message.edit_text(call.message.text + extra)
    except Exception:
        pass


async def download_excel(message, max_mb: int = 20):
    doc = message.document
    if not doc.file_name.lower().endswith((".xlsx", ".xls")):
        return None, "❌ Bu Excel fayl emas (.xlsx kerak)."
    if doc.file_size and doc.file_size > max_mb * 1024 * 1024:
        return None, f"❌ Fayl juda katta ({max_mb} MB dan oshmasin)."
    try:
        file = await message.bot.get_file(doc.file_id)
        buffer = io.BytesIO()
        await message.bot.download_file(file.file_path, buffer)
        buffer.seek(0)
        df = pd.read_excel(buffer)
        return df, None
    except Exception as e:
        return None, f"❌ Faylni o'qishda xato: {e}"


def make_excel(rows: list[dict], sheet_name: str = "Sheet1") -> io.BytesIO:
    """Lug'atlar ro'yxatidan .xlsx fayl (BytesIO) yasaydi."""
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer


def safe_int(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        return int(float(value))
    except (ValueError, TypeError):
        return None


def safe_float(value):
    try:
        if value is None:
            return None
        f = float(value)
        if math.isnan(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def money(value: float) -> str:
    return f"{value:,.0f}"
