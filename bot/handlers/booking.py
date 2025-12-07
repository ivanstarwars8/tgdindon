"""Хендлеры, отвечающие за процесс бронирования занятия."""

import datetime as dt
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from bot.config import Config
from bot.database.queries import Database
from bot.keyboards.inline import confirmation_keyboard, direction_keyboard, slots_keyboard
from bot.utils import google_calendar
from bot.utils.scheduler import schedule_booking_reminders

router = Router()


class BookingForm(StatesGroup):
    direction = State()
    slot = State()


async def _load_slots(bot: Bot, config: Config):
    """Получить список свободных слотов из Google Calendar."""
    service = bot["calendar_service"]
    slots = await google_calendar.get_free_slots(
        service=service,
        calendar_id=config.calendar_id,
        timezone=config.timezone,
    )
    return slots


@router.callback_query(F.data.startswith("dir:"))
async def direction_selected(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Пользователь выбрал направление — запрашиваем ближайшие свободные слоты."""
    direction = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(direction=direction)
    config: Config = bot["config"]
    slots = await _load_slots(bot, config)
    await callback.message.edit_text(
        f"Вы выбрали направление: {direction}.\nВыберите время:",
        reply_markup=slots_keyboard(slots[:10], config.timezone),
    )
    await state.set_state(BookingForm.slot)
    await callback.answer()


@router.callback_query(F.data == "slots:refresh")
async def refresh_slots(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Обновить список свободных слотов, не сбрасывая выбор направления."""
    data = await state.get_data()
    direction = data.get("direction", "направление")
    config: Config = bot["config"]
    slots = await _load_slots(bot, config)
    await callback.message.edit_text(
        f"Направление: {direction}.\nВыберите время:",
        reply_markup=slots_keyboard(slots[:10], config.timezone),
    )
    await callback.answer("Свободные слоты обновлены")


@router.callback_query(BookingForm.slot, F.data.startswith("slot:"))
async def slot_selected(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Пользователь кликнул на слот — переводим в состояние подтверждения."""
    config: Config = bot["config"]
    slot_text = callback.data.split(":", maxsplit=1)[1]
    selected_dt = dt.datetime.fromisoformat(slot_text)
    tzinfo = ZoneInfo(config.timezone)
    start = selected_dt.astimezone(tzinfo)
    end = start + dt.timedelta(minutes=60)

    await state.update_data(slot=start.isoformat(), end=end.isoformat())
    data = await state.get_data()
    direction = data.get("direction")

    text = (
        f"Подтвердите запись:\n"
        f"Направление: {direction}\n"
        f"Дата и время: {start.astimezone(tzinfo).strftime('%d.%m %H:%M')}\n"
        f"Стоимость: 2000 ₽ (" + config.payment_note + ")"
    )
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard())
    await callback.answer()


@router.callback_query(BookingForm.slot, F.data == "confirm:no")
async def cancel_booking(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена бронирования из шага подтверждения."""
    await state.clear()
    await callback.message.edit_text("Бронирование отменено.", reply_markup=direction_keyboard())
    await callback.answer()


@router.callback_query(BookingForm.slot, F.data == "confirm:yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Финальный шаг: создаём событие в календаре и сохраняем бронь в БД."""
    data = await state.get_data()
    config: Config = bot["config"]
    db: Database = bot["db"]
    scheduler = bot["scheduler"]

    direction = data.get("direction")
    start = dt.datetime.fromisoformat(data["slot"])
    end = dt.datetime.fromisoformat(data["end"])

    service = bot["calendar_service"]
    summary = f"Занятие: {direction}"
    description = f"Ученик: @{callback.from_user.username or callback.from_user.id}"
    # Создание события — вынесено в utils, чтобы можно было заменить реализацию.
    event_id = await google_calendar.create_event(
        service=service,
        calendar_id=config.calendar_id,
        start=start,
        end=end,
        summary=summary,
        description=description,
        timezone=config.timezone,
    )

    booking_id = await db.create_booking(
        user_id=callback.from_user.id,
        direction=direction,
        start_time=start,
        end_time=end,
        price=2000,
        calendar_event_id=event_id,
    )

    await state.clear()

    tzinfo = ZoneInfo(config.timezone)
    confirmation_text = (
        f"Запись подтверждена!\n"
        f"Номер брони: {booking_id}\n"
        f"Направление: {direction}\n"
        f"Дата и время: {start.astimezone(tzinfo).strftime('%d.%m %H:%M')}\n"
        f"Стоимость: 2000 ₽ (" + config.payment_note + ")"
    )
    await callback.message.edit_text(confirmation_text)

    booking = await db.get_booking(booking_id)
    if booking:
        # Планируем два напоминания: за сутки и за час до начала.
        schedule_booking_reminders(scheduler, bot, booking, config.timezone)

    await callback.answer("Занятие добавлено в календарь")
