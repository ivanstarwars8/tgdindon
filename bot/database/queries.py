import aiosqlite
from datetime import datetime
from typing import List, Optional

from .models import Booking


class Database:
    def __init__(self, path: str):
        self.path = path

    async def setup(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    calendar_event_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    comment TEXT
                );
                """
            )
            await db.commit()

    async def create_booking(
        self,
        user_id: int,
        direction: str,
        start_time: datetime,
        end_time: datetime,
        price: int,
        calendar_event_id: str,
        comment: Optional[str] = None,
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO bookings (
                    user_id, direction, start_time, end_time, price, calendar_event_id, created_at, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    direction,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    price,
                    calendar_event_id,
                    datetime.utcnow().isoformat(),
                    comment,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def list_user_bookings(self, user_id: int) -> List[Booking]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, user_id, direction, start_time, end_time, price, calendar_event_id, created_at, comment FROM bookings WHERE user_id=? ORDER BY start_time",
                (user_id,),
            )
            rows = await cursor.fetchall()
        return [self._row_to_booking(row) for row in rows]

    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, user_id, direction, start_time, end_time, price, calendar_event_id, created_at, comment FROM bookings WHERE id=?",
                (booking_id,),
            )
            row = await cursor.fetchone()
        return self._row_to_booking(row) if row else None

    async def delete_booking(self, booking_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "DELETE FROM bookings WHERE id=? AND user_id=?",
                (booking_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def list_upcoming_bookings(self, until: datetime) -> List[Booking]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, user_id, direction, start_time, end_time, price, calendar_event_id, created_at, comment FROM bookings WHERE start_time>=? AND start_time<=? ORDER BY start_time",
                (datetime.utcnow().isoformat(), until.isoformat()),
            )
            rows = await cursor.fetchall()
        return [self._row_to_booking(row) for row in rows]

    def _row_to_booking(self, row) -> Booking:
        return Booking(
            id=row[0],
            user_id=row[1],
            direction=row[2],
            start_time=datetime.fromisoformat(row[3]),
            end_time=datetime.fromisoformat(row[4]),
            price=row[5],
            calendar_event_id=row[6],
            created_at=datetime.fromisoformat(row[7]),
            comment=row[8],
        )
