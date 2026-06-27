from aiogram.fsm.state import State, StatesGroup


class GroupFSM(StatesGroup):
    name = State(); year = State(); price = State()


class StudentFSM(StatesGroup):
    name = State(); last_name = State(); tel = State(); group_id = State()


class DebtFSM(StatesGroup):
    search = State(); select = State(); amount = State()


class WarningFSM(StatesGroup):
    text = State()


class UserCheckFSM(StatesGroup):
    search = State()


class PaymentFSM(StatesGroup):
    search = State(); select = State(); check = State()


class ConfirmFSM(StatesGroup):
    amount = State()


class YearFSM(StatesGroup):
    year = State()


class ExcelFSM(StatesGroup):
    file = State()


class TestFSM(StatesGroup):
    year = State(); file = State()


class PublicUploadFSM(StatesGroup):
    file = State(); caption = State()


class PublicTestFSM(StatesGroup):
    file = State(); caption = State()


class RatingFSM(StatesGroup):
    search = State()


class HistoryFSM(StatesGroup):
    search = State()


class ContactFSM(StatesGroup):
    text = State()
    ask_extra = State()
    extra = State()


class MonthlyFSM(StatesGroup):
    confirm = State()


class AttendanceFSM(StatesGroup):
    year = State()
    group = State()
    mode = State()
    marking = State()
    confirm = State()
    file = State()


class CardFSM(StatesGroup):
    name = State()
    card = State()
    tel = State()
