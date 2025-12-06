from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import Config
from bot.database.queries import Database
from bot.keyboards.inline import lessons_keyboard
from bot.utils import google_calendar

router = Router()


@router.message(Command("my_lessons"))
async def list_lessons(message: Message, bot: Bot) -> None:
    db: Database = bot["db"]
    bookings = await db.list_user_bookings(message.from_user.id)
    if not bookings:
        await message.answer("У вас пока нет записей.")
        return

    lines = [
        "Ваши записи:",
    ]
    for booking in bookings:
        lines.append(
            f"#{booking.id} • {booking.direction} • {booking.start_time:%d.%m %H:%M}"
        )
    await message.answer("\n".join(lines), reply_markup=lessons_keyboard([b.id for b in bookings]))


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_lesson(callback: CallbackQuery, bot: Bot) -> None:
    booking_id = int(callback.data.split(":", maxsplit=1)[1])
    db: Database = bot["db"]
    config: Config = bot["config"]
    booking = await db.get_booking(booking_id)
    if not booking or booking.user_id != callback.from_user.id:
        await callback.answer("Бронь не найдена")
        return

    service = bot["calendar_service"]
    await google_calendar.delete_event(service, config.calendar_id, booking.calendar_event_id)
    await db.delete_booking(booking_id, callback.from_user.id)
    await callback.message.edit_text(f"Запись #{booking_id} отменена")
    await callback.answer("Удалено из календаря")
