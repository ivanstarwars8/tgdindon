from __future__ import annotations

import datetime as dt
from typing import List, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def build_calendar_service(credentials_file: str):
    credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def get_free_slots(
    service,
    calendar_id: str,
    timezone: str,
    days_ahead: int = 7,
    slot_length_minutes: int = 60,
) -> List[dt.datetime]:
    """Fetch free time slots from Google Calendar using the FreeBusy API."""
    now = dt.datetime.now(dt.timezone.utc)
    end = now + dt.timedelta(days=days_ahead)

    body = {
        "timeMin": now.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": timezone,
        "items": [{"id": calendar_id}],
    }
    freebusy = service.freebusy().query(body=body).execute()
    busy_periods = freebusy["calendars"][calendar_id].get("busy", [])

    busy_blocks: List[Tuple[dt.datetime, dt.datetime]] = []
    for period in busy_periods:
        busy_blocks.append(
            (
                dt.datetime.fromisoformat(period["start"]),
                dt.datetime.fromisoformat(period["end"]),
            )
        )

    slots: List[dt.datetime] = []
    current = now.replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
    while current < end:
        candidate_end = current + dt.timedelta(minutes=slot_length_minutes)
        overlaps = any(start < candidate_end and current < end_ for start, end_ in busy_blocks)
        if not overlaps:
            slots.append(current)
        current += dt.timedelta(minutes=slot_length_minutes)
    return slots


def create_event(
    service,
    calendar_id: str,
    start: dt.datetime,
    end: dt.datetime,
    summary: str,
    description: str,
    timezone: str,
) -> str:
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": timezone},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 24 * 60},
            ],
        },
    }
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created_event["id"]


def delete_event(service, calendar_id: str, event_id: str) -> None:
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
