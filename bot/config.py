"""Загрузка конфигурации бота из переменных окружения/.env."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    calendar_id: str
    credentials_file: str
    database_path: str = "bot.db"
    timezone: str = "UTC"
    payment_note: str = "Оплата при встрече"
    admin_chat_id: Optional[int] = None


def load_config() -> Config:
    """Load configuration from environment variables."""
    bot_token = os.getenv("BOT_TOKEN")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    database_path = os.getenv("DATABASE_PATH", "bot.db")
    timezone = os.getenv("TIMEZONE", "UTC")
    payment_note = os.getenv("PAYMENT_NOTE", "Оплата при встрече")
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID")) if os.getenv("ADMIN_CHAT_ID") else None

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")
    if not calendar_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID is required")

    return Config(
        bot_token=bot_token,
        calendar_id=calendar_id,
        credentials_file=credentials_file,
        database_path=database_path,
        timezone=timezone,
        payment_note=payment_note,
        admin_chat_id=admin_chat_id,
    )
