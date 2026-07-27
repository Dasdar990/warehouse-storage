"""
Single source of truth for "what time is it" across the backend.

Everything that timestamps something (movements, user creation, JWT
expiry, barcode prefixes, activity-log date filters) should go through
`now_rome()` / `APP_TZ` here instead of calling `datetime.now(timezone.utc)`
directly, so the whole app agrees on one timezone: Europe/Rome.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Europe/Rome")


def now_rome() -> datetime:
    """Current time as a timezone-aware datetime in Europe/Rome (handles
    the CET/CEST daylight-saving switch automatically)."""
    return datetime.now(APP_TZ)
