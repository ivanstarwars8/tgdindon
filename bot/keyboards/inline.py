import datetime as dt
from typing import Iterable, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from zoneinfo import ZoneInfo


DIRECTIONS = [
    "Математика",
    "Физика",
    "Программирование",
    "Химия",
    "Английский",
]


def direction_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for direction in DIRECTIONS:
        builder.button(text=direction, callback_data=f"dir:{direction}")
    builder.adjust(2)
    return builder.as_markup()


def slots_keyboard(slots: Iterable[dt.datetime], timezone: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tzinfo = ZoneInfo(timezone)
    for slot in slots:
        label = slot.astimezone(tzinfo).strftime("%d.%m %H:%M")
        builder.button(text=label, callback_data=f"slot:{slot.isoformat()}")
    builder.button(text="Обновить", callback_data="slots:refresh")
    builder.adjust(2)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data="confirm:yes")
    builder.button(text="Отмена", callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()


def lessons_keyboard(bookings: List[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for booking_id in bookings:
        builder.button(text=f"Отменить #{booking_id}", callback_data=f"cancel:{booking_id}")
    if not bookings:
        builder.button(text="Нет записей", callback_data="noop")
    builder.adjust(1)
    return builder.as_markup()
