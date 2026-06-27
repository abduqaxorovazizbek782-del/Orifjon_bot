import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///crm_lms.db")
GROUP_IDS = [int(x) for x in os.getenv("GROUP_IDS", "").split(",") if x.strip()]

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi. .env faylni tekshiring.")

PAYMENT_CARDS = [
    ("Azizbek Abduqaxorov", "9860 3501 4123 5027", "+998 97 070 3502"),
]


def cards_text() -> str:
    lines = ["💳 <b>To'lov uchun karta ma'lumotlari:</b>\n"]
    for name, card, tel in PAYMENT_CARDS:
        lines.append(f"🧑 {name}\n💳 <code>{card}</code>\n📞 {tel}\n")
    return "\n".join(lines)
