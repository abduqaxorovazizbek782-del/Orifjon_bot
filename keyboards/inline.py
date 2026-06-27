from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def groups_kb(groups, prefix="grp") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for g in groups:
        b.button(text=f"{g.name} [{g.year}] ({g.monthly_price:,.0f})",
                 callback_data=f"{prefix}:{g.id}")
    b.adjust(1)
    return b.as_markup()


def student_remove_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Remove", callback_data=f"remove:{student_id}")]
    ])


def student_remove_confirm_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=f"delok:{student_id}"),
         InlineKeyboardButton(text="🔙 Yo'q", callback_data=f"delno:{student_id}")]
    ])


def students_select_kb(students, prefix="pick") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in students:
        grp = getattr(s, "group", None)
        if grp:
            extra = f" • {grp.name} [{grp.year}]"
        else:
            extra = " • (guruhsiz)"
        b.button(text=f"{s.name} {s.last_name}{extra}",
                 callback_data=f"{prefix}:{s.id}")
    b.adjust(1)
    return b.as_markup()


def pay_now_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov qilish", callback_data=f"paynow:{student_id}")]
    ])


def payment_decision_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{req_id}"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{req_id}")]
    ])


def monthly_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, hammaga yozilsin",
                              callback_data="monthly_yes"),
         InlineKeyboardButton(text="❌ Bekor qilish",
                              callback_data="monthly_no")]
    ])


def monthly_final_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, aniq yozilsin",
                              callback_data="monthly_final_yes"),
         InlineKeyboardButton(text="❌ Bekor qilish",
                              callback_data="monthly_final_no")]
    ])


# ───────────── DAVOMAT ─────────────

def attendance_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Bittalab belgilash", callback_data="att_mode:one")],
        [InlineKeyboardButton(text="📥 Excel orqali", callback_data="att_mode:excel")],
    ])


def attendance_marking_kb(students, absent_ids) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in students:
        mark = "❌" if s.id in absent_ids else "✅"
        b.button(text=f"{mark} {s.name} {s.last_name}",
                 callback_data=f"att_toggle:{s.id}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="💾 Saqlash", callback_data="att_save"))
    b.row(InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="att_cancel"))
    return b.as_markup()


def attendance_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, saqlansin", callback_data="att_confirm_yes"),
         InlineKeyboardButton(text="❌ Yo'q", callback_data="att_confirm_no")]
    ])


# ───────────── TO'LOV KARTALARI ─────────────

def cards_manage_kb(cards) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for c in cards:
        b.button(text=f"🗑 {c.name} • {c.card}", callback_data=f"card_del:{c.id}")
    b.adjust(1)
    if len(cards) < 4:
        b.row(InlineKeyboardButton(text="➕ Yangi karta qo'shish",
                                   callback_data="card_add"))
    return b.as_markup()


def card_del_confirm_kb(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirilsin",
                              callback_data=f"card_delok:{card_id}"),
         InlineKeyboardButton(text="🔙 Yo'q",
                              callback_data=f"card_delno:{card_id}")]
    ])
