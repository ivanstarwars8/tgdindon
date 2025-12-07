from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.inline import direction_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я бот для записи на занятия. Выберите направление, чтобы подобрать время."
    )
    await message.answer(text, reply_markup=direction_keyboard())
