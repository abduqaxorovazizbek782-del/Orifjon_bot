from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from sqlalchemy.pool import AsyncAdaptedQueuePool

from config import DATABASE_URL
from database.models import Base

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Har bir yangi SQLite ulanishi uchun WAL va boshqa optimizatsiyalar
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")        # ko'p o'qish/yozish, qotmaydi
    cursor.execute("PRAGMA synchronous=NORMAL;")      # tez, ammo xavfsiz
    cursor.execute("PRAGMA busy_timeout=10000;")      # band bo'lsa 10s kutadi (lock xatosi yo'q)
    cursor.execute("PRAGMA foreign_keys=ON;")         # FK qoidalari ishlaydi
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.execute("PRAGMA cache_size=-20000;")       # ~20MB kesh
    cursor.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
