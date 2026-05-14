"""
In-memory frequency capping.
Tracks impressions per user per line item within a rolling time window.
Swap the _store dict for Redis (INCR + EXPIRE) in production.
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta


# {(user_id, line_item_id): [(timestamp), ...]}
_impression_log: dict[tuple[str, str], list[datetime]] = defaultdict(list)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_impression(user_id: str, line_item_id: str) -> None:
    _impression_log[(user_id, line_item_id)].append(_now())


def is_frequency_capped(user_id: str, line_item_id: str, max_impressions: int, period_hours: int) -> bool:
    key = (user_id, line_item_id)
    cutoff = _now() - timedelta(hours=period_hours)

    recent = [ts for ts in _impression_log[key] if ts >= cutoff]
    _impression_log[key] = recent  # prune stale entries

    return len(recent) >= max_impressions


def get_impression_count(user_id: str, line_item_id: str, period_hours: int) -> int:
    key = (user_id, line_item_id)
    cutoff = _now() - timedelta(hours=period_hours)
    return sum(1 for ts in _impression_log[key] if ts >= cutoff)
