from datetime import datetime, timezone, date
from sqlalchemy import (
    BigInteger, Integer, String, Float, DateTime, Date, ForeignKey, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    monthly_price: Mapped[float] = mapped_column(Float, default=0.0)
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=2025)
    students: Mapped[list["Student"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tel: Mapped[str] = mapped_column(String(20), nullable=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    average_score: Mapped[float] = mapped_column(Float, default=0.0)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    group: Mapped["Group"] = relationship(back_populates="students")
    test_results: Mapped[list["TestResult"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class TestResult(Base):
    __tablename__ = "test_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    student: Mapped["Student"] = relationship(back_populates="test_results")


class BotUser(Base):
    __tablename__ = "bot_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(300), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), default="document")
    file_name: Mapped[str] = mapped_column(String(200), nullable=True)
    caption: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class TestArchive(Base):
    __tablename__ = "test_archive"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(300), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), default="document")
    file_name: Mapped[str] = mapped_column(String(200), nullable=True)
    caption: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class MonthlyBilling(Base):
    __tablename__ = "monthly_billings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    students_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint("student_id", "day", name="uq_attendance_student_day"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    present: Mapped[int] = mapped_column(Integer, default=0)  # 1=keldi, 0=kelmadi
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    student: Mapped["Student"] = relationship(back_populates="attendances")


class PaymentCard(Base):
    __tablename__ = "payment_cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    card: Mapped[str] = mapped_column(String(50), nullable=False)
    tel: Mapped[str] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
