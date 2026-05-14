from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.campaign import (
    Campaign, CampaignCreate, CampaignStatus,
    LineItem, LineItemCreate,
)
from app.services import campaign_service

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=Campaign, status_code=201)
def create_campaign(payload: CampaignCreate):
    return campaign_service.create_campaign(payload)


@router.get("/", response_model=list[Campaign])
def list_campaigns(
    advertiser_id: Optional[str] = Query(None),
    status: Optional[CampaignStatus] = Query(None),
):
    return campaign_service.list_campaigns(advertiser_id=advertiser_id, status=status)


@router.get("/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: str):
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return campaign


@router.patch("/{campaign_id}/status", response_model=Campaign)
def update_status(campaign_id: str, status: CampaignStatus):
    result = campaign_service.update_campaign_status(campaign_id, status)
    if not result:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return result


@router.post("/{campaign_id}/line-items", response_model=LineItem, status_code=201)
def add_line_item(campaign_id: str, payload: LineItemCreate):
    li = campaign_service.add_line_item(campaign_id, payload)
    if not li:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return li
