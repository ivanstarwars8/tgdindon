import datetime as dt
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from bot.database.models import Booking


REMINDER_OFFSETS = (24 * 60, 60)


async def send_reminder(bot: Bot, booking: Booking, before: str) -> None:
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
    tzinfo = ZoneInfo(timezone)
    for minutes_before in REMINDER_OFFSETS:
        remind_at = booking.start_time.astimezone(tzinfo) - dt.timedelta(minutes=minutes_before)
        if remind_at <= dt.datetime.now(remind_at.tzinfo or dt.timezone.utc):
            continue
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=remind_at, timezone=tzinfo),
            args=(bot, booking, _format_minutes(minutes_before)),
            id=_build_job_id(booking.id, minutes_before),
            replace_existing=True,
        )


def cancel_booking_reminders(
    scheduler: AsyncIOScheduler,
    booking_id: int,
) -> None:
    for minutes_before in REMINDER_OFFSETS:
        try:
            scheduler.remove_job(_build_job_id(booking_id, minutes_before))
        except JobLookupError:
            continue


def build_scheduler(bot: Bot, timezone: str) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(timezone))
    scheduler.start()
    return scheduler


def _format_minutes(minutes: int) -> str:
    if minutes >= 60:
        hours = minutes // 60
        return f"{hours} ч" if minutes % 60 == 0 else f"{hours} ч {minutes % 60} мин"
    return f"{minutes} мин"


def _build_job_id(booking_id: int, minutes_before: int) -> str:
    return f"reminder-{booking_id}-{minutes_before}"
