"""Структуры данных для слоя базы."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Booking:
    """Представление записи занятия, сохраняемой в SQLite."""

    id: int
    user_id: int
    direction: str
    start_time: datetime
    end_time: datetime
    price: int
    calendar_event_id: str
    created_at: datetime
    comment: Optional[str] = None
