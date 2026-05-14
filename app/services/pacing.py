"""
Budget pacing engine.
Tracks spend per campaign and line item, resets daily budgets at midnight UTC.
In production: use atomic Redis increments or a PostgreSQL ledger.
"""

from datetime import datetime, timezone
from app.models.campaign import Campaign, Budget


_campaign_spend: dict[str, float] = {}       # campaign_id -> total spent USD
_daily_spend: dict[str, float] = {}          # campaign_id -> today's spend
_last_reset: dict[str, str] = {}             # campaign_id -> YYYY-MM-DD


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_daily_if_needed(campaign_id: str) -> None:
    today = _today()
    if _last_reset.get(campaign_id) != today:
        _daily_spend[campaign_id] = 0.0
        _last_reset[campaign_id] = today


def get_spend(campaign_id: str) -> tuple[float, float]:
    """Returns (total_spend, daily_spend)."""
    _reset_daily_if_needed(campaign_id)
    return _campaign_spend.get(campaign_id, 0.0), _daily_spend.get(campaign_id, 0.0)


def record_spend(campaign_id: str, cpm_usd: float) -> None:
    """Record a winning bid impression (CPM / 1000 = cost per impression)."""
    cost = cpm_usd / 1000.0
    _reset_daily_if_needed(campaign_id)
    _campaign_spend[campaign_id] = _campaign_spend.get(campaign_id, 0.0) + cost
    _daily_spend[campaign_id] = _daily_spend.get(campaign_id, 0.0) + cost


def has_budget(campaign: Campaign) -> bool:
    _reset_daily_if_needed(campaign.id)
    total_spent = _campaign_spend.get(campaign.id, 0.0)
    daily_spent = _daily_spend.get(campaign.id, 0.0)

    if total_spent >= campaign.budget.total_budget_usd:
        return False
    if campaign.budget.daily_budget_usd and daily_spent >= campaign.budget.daily_budget_usd:
        return False
    return True


def pace_bid(campaign: Campaign, base_cpm: float) -> float:
    """
    Smooth pacing: scale bid price down if we're spending ahead of schedule.
    Uses a simple time-of-day pacing ratio.
    """
    if not campaign.budget.daily_budget_usd:
        return base_cpm

    now = datetime.now(timezone.utc)
    day_fraction = (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    budget_fraction = _daily_spend.get(campaign.id, 0.0) / campaign.budget.daily_budget_usd

    if budget_fraction > day_fraction + 0.1:
        # Spending too fast — throttle bids
        scale = max(0.5, day_fraction / (budget_fraction + 0.01))
        return base_cpm * scale

    return base_cpm
