# -*- coding: utf-8 -*-
"""
Timezone-aware datetime helpers.
"""

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def isoformat_utc(dt: datetime) -> str | None:
    if dt is None:
        return None
    return ensure_utc(dt).isoformat()
