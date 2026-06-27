from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.buttons import (
    BTN_NEW_GROUP, BTN_YEAR_GROUPS, BTN_ADD_STUDENT, BTN_EXCEL_UPLOAD,
    BTN_STUDENT_LIST, BTN_DEBT, BTN_MONTHLY, BTN_TEST_UPLOAD,
    BTN_PUBLIC_UPLOAD, BTN_PUBLIC_TEST, BTN_DEBTORS_EXCEL, BTN_ATTENDANCE,
    BTN_IDS_EXCEL, BTN_PAYMENT_CARDS,
    BTN_CHECK_BALANCE, BTN_PAY, BTN_RATING, BTN_HISTORY, BTN_FILES,
    BTN_TEST_ARCHIVE, BTN_CONTACT_ADMIN,
)

MENU_BUTTONS = {
    BTN_NEW_GROUP, BTN_YEAR_GROUPS, BTN_ADD_STUDENT, BTN_EXCEL_UPLOAD,
    BTN_STUDENT_LIST, BTN_DEBT, BTN_MONTHLY, BTN_TEST_UPLOAD,
    BTN_PUBLIC_UPLOAD, BTN_PUBLIC_TEST, BTN_DEBTORS_EXCEL, BTN_ATTENDANCE,
    BTN_IDS_EXCEL, BTN_PAYMENT_CARDS,
    BTN_CHECK_BALANCE, BTN_PAY, BTN_RATING, BTN_HISTORY, BTN_FILES,
    BTN_TEST_ARCHIVE, BTN_CONTACT_ADMIN,
}


class MenuResetMiddleware(BaseMiddleware):
    """Menyu tugmasi bosilsa, oldingi tugatilmagan FSM oqimini tozalaydi."""

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text in MENU_BUTTONS:
            state: FSMContext | None = data.get("state")
            if state is not None and await state.get_state() is not None:
                await state.clear()
        return await handler(event, data)
