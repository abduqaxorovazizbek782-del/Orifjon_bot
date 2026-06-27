import os
import logging
from datetime import datetime

from config import DATABASE_URL

logger = logging.getLogger(__name__)

BACKUP_DIR = "backups"
KEEP_DAYS = 7


def _db_path() -> str | None:
    if "sqlite" not in DATABASE_URL:
        return None
    path = DATABASE_URL.split("///")[-1]
    return path or None


def make_backup() -> str | None:
    """Bazadan nusxa oladi. Backup fayl yo'lini qaytaradi (yoki None)."""
    try:
        src = _db_path()
        if not src or not os.path.exists(src):
            logger.warning("⚠️ Backup: baza fayli topilmadi (%s).", src)
            return None

        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(BACKUP_DIR, f"backup_{stamp}.db")

        import sqlite3
        # timeout — bot yozayotgan bo'lsa kutadi (lock xatosi bo'lmaydi)
        source = sqlite3.connect(src, timeout=30)
        dest = sqlite3.connect(dst)
        with dest:
            source.backup(dest)
        source.close()
        dest.close()

        logger.info("✅ Backup tayyor: %s", dst)
        _cleanup_old()
        return dst
    except Exception as e:
        logger.error("❌ Backup xatosi: %s", e)
        return None


def _cleanup_old() -> None:
    try:
        now = datetime.now().timestamp()
        for name in os.listdir(BACKUP_DIR):
            if not name.startswith("backup_"):
                continue
            path = os.path.join(BACKUP_DIR, name)
            if now - os.path.getmtime(path) > KEEP_DAYS * 86400:
                os.remove(path)
                logger.info("🗑 Eski backup o'chirildi: %s", name)
    except Exception as e:
        logger.error("❌ Backup tozalashda xato: %s", e)
