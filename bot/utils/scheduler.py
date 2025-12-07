"""Настройка напоминаний о занятиях."""

import datetime as dt
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot

from bot.database.models import Booking


async def send_reminder(bot: Bot, booking: Booking, before: str) -> None:
    """Сообщение пользователю за заданное время до занятия."""
    text = (
        f"Напоминание: занятие по {booking.direction} начнётся через {before}.\n"
        f"Начало: {booking.start_time:%d.%m %H:%M}"
    )
    await bot.send_message(chat_id=booking.user_id, text=text)


def schedule_booking_reminders(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    booking: Booking,
    timezone: str,
) -> None:
    """Создать два одноразовых задания напоминания (24 часа и 1 час)."""
    tzinfo = ZoneInfo(timezone)
    for minutes_before in (24 * 60, 60):
        remind_at = booking.start_time.astimezone(tzinfo) - dt.timedelta(minutes=minutes_before)
        if remind_at <= dt.datetime.now(remind_at.tzinfo or dt.timezone.utc):
            continue
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=remind_at, timezone=tzinfo),
            args=(bot, booking, _format_minutes(minutes_before)),
            id=f"reminder-{booking.id}-{minutes_before}",
            replace_existing=True,
        )


def build_scheduler(bot: Bot, timezone: str) -> AsyncIOScheduler:
    """Создать и запустить AsyncIOScheduler с заданной таймзоной."""
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(timezone))
    scheduler.start()
    return scheduler


def _format_minutes(minutes: int) -> str:
    """Удобочитаемое представление количества минут."""
    if minutes >= 60:
        hours = minutes // 60
        return f"{hours} ч" if minutes % 60 == 0 else f"{hours} ч {minutes % 60} мин"
    return f"{minutes} мин"
