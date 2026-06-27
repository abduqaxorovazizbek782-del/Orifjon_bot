from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.buttons import (
    BTN_NEW_GROUP, BTN_YEAR_GROUPS, BTN_ADD_STUDENT, BTN_EXCEL_UPLOAD,
    BTN_STUDENT_LIST, BTN_DEBT, BTN_MONTHLY, BTN_TEST_UPLOAD,
    BTN_PUBLIC_UPLOAD, BTN_PUBLIC_TEST, BTN_DEBTORS_EXCEL, BTN_ATTENDANCE,
    BTN_IDS_EXCEL, BTN_PAYMENT_CARDS, BTN_STUDENTS_REPORT,
    BTN_CHECK_BALANCE, BTN_PAY, BTN_RATING, BTN_HISTORY, BTN_FILES,
    BTN_TEST_ARCHIVE, BTN_CONTACT_ADMIN,
)


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_NEW_GROUP), KeyboardButton(text=BTN_YEAR_GROUPS)],
            [KeyboardButton(text=BTN_ADD_STUDENT), KeyboardButton(text=BTN_EXCEL_UPLOAD)],
            [KeyboardButton(text=BTN_STUDENT_LIST), KeyboardButton(text=BTN_DEBT)],
            [KeyboardButton(text=BTN_MONTHLY), KeyboardButton(text=BTN_TEST_UPLOAD)],
            [KeyboardButton(text=BTN_ATTENDANCE), KeyboardButton(text=BTN_DEBTORS_EXCEL)],
            [KeyboardButton(text=BTN_IDS_EXCEL), KeyboardButton(text=BTN_STUDENTS_REPORT)],
            [KeyboardButton(text=BTN_PAYMENT_CARDS)],
            [KeyboardButton(text=BTN_PUBLIC_UPLOAD), KeyboardButton(text=BTN_PUBLIC_TEST)],
        ],
        resize_keyboard=True,
    )


def user_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CHECK_BALANCE), KeyboardButton(text=BTN_PAY)],
            [KeyboardButton(text=BTN_RATING), KeyboardButton(text=BTN_HISTORY)],
            [KeyboardButton(text=BTN_TEST_ARCHIVE), KeyboardButton(text=BTN_FILES)],
            [KeyboardButton(text=BTN_CONTACT_ADMIN)],
        ],
        resize_keyboard=True,
    )
