"""Inline-клавиатуры, используемые в боте."""

import datetime as dt
from typing import Iterable, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from zoneinfo import ZoneInfo


# Набор направлений, отображаемых на первом экране.
DIRECTIONS = [
    "Математика",
    "Физика",
    "Программирование",
    "Химия",
    "Английский",
]


def direction_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с направлениями обучения."""
    builder = InlineKeyboardBuilder()
    for direction in DIRECTIONS:
        builder.button(text=direction, callback_data=f"dir:{direction}")
    builder.adjust(2)
    return builder.as_markup()


def slots_keyboard(slots: Iterable[dt.datetime], timezone: str) -> InlineKeyboardMarkup:
    """Слоты отображаются локализованными метками, а callback хранит ISO-дату."""
    builder = InlineKeyboardBuilder()
    tzinfo = ZoneInfo(timezone)
    for slot in slots:
        label = slot.astimezone(tzinfo).strftime("%d.%m %H:%M")
        builder.button(text=label, callback_data=f"slot:{slot.isoformat()}")
    builder.button(text="Обновить", callback_data="slots:refresh")
    builder.adjust(2)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения/отмены перед записью."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data="confirm:yes")
    builder.button(text="Отмена", callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()


def lessons_keyboard(bookings: List[int]) -> InlineKeyboardMarkup:
    """Список кнопок для отмены конкретных записей пользователя."""
    builder = InlineKeyboardBuilder()
    for booking_id in bookings:
        builder.button(text=f"Отменить #{booking_id}", callback_data=f"cancel:{booking_id}")
    if not bookings:
        builder.button(text="Нет записей", callback_data="noop")
    builder.adjust(1)
    return builder.as_markup()
