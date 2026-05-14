from datetime import datetime, timezone
from typing import Optional

from app.models.campaign import (
    Campaign, CampaignCreate, CampaignStatus,
    LineItem, LineItemCreate,
    new_campaign_id, new_lineitem_id,
)


_campaigns: dict[str, Campaign] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_campaign(payload: CampaignCreate) -> Campaign:
    campaign = Campaign(
        id=new_campaign_id(),
        name=payload.name,
        advertiser_id=payload.advertiser_id,
        status=CampaignStatus.DRAFT,
        budget=payload.budget,
        targeting=payload.targeting,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_at=_now(),
        updated_at=_now(),
    )
    _campaigns[campaign.id] = campaign
    return campaign


def get_campaign(campaign_id: str) -> Optional[Campaign]:
    return _campaigns.get(campaign_id)


def list_campaigns(advertiser_id: Optional[str] = None, status: Optional[CampaignStatus] = None) -> list[Campaign]:
    results = list(_campaigns.values())
    if advertiser_id:
        results = [c for c in results if c.advertiser_id == advertiser_id]
    if status:
        results = [c for c in results if c.status == status]
    return results


def update_campaign_status(campaign_id: str, status: CampaignStatus) -> Optional[Campaign]:
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        return None
    campaign.status = status
    campaign.updated_at = _now()
    return campaign


def add_line_item(campaign_id: str, payload: LineItemCreate) -> Optional[LineItem]:
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        return None

    line_item = LineItem(
        id=new_lineitem_id(),
        campaign_id=campaign_id,
        name=payload.name,
        status=CampaignStatus.DRAFT,
        bidding_strategy=payload.bidding_strategy,
        max_cpm_usd=payload.max_cpm_usd,
        creative_ids=payload.creative_ids,
        targeting=payload.targeting,
        start_date=payload.start_date,
        end_date=payload.end_date,
        priority=payload.priority,
        created_at=_now(),
        updated_at=_now(),
    )
    campaign.line_items.append(line_item)
    campaign.updated_at = _now()
    return line_item


def get_active_line_items() -> list[tuple[Campaign, LineItem]]:
    """Return all active campaigns + active line items eligible to bid."""
    now = _now()
    results = []
    for campaign in _campaigns.values():
        if campaign.status != CampaignStatus.ACTIVE:
            continue
        if now < campaign.start_date or now > campaign.end_date:
            continue
        for li in campaign.line_items:
            if li.status != CampaignStatus.ACTIVE:
                continue
            if now < li.start_date or now > li.end_date:
                continue
            results.append((campaign, li))
    return sorted(results, key=lambda x: x[1].priority)
