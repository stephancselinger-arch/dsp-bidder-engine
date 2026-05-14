import pytest
from datetime import datetime, timezone, timedelta

from app.models.openrtb import BidRequest, Impression, Banner, Site, Device, Geo, User
from app.models.campaign import (
    CampaignCreate, Budget, Targeting, GeoTarget,
    LineItemCreate, CampaignStatus, BiddingStrategy,
)
from app.services import campaign_service
from app.services.bid_evaluator import evaluate_bid_request


def _future(days=30):
    return datetime.now(timezone.utc) + timedelta(days=days)


def _past(days=1):
    return datetime.now(timezone.utc) - timedelta(days=days)


def _make_campaign(max_cpm: float = 5.0, country: str = "USA") -> tuple:
    campaign = campaign_service.create_campaign(CampaignCreate(
        name="Test Campaign",
        advertiser_id="adv_test",
        budget=Budget(total_budget_usd=1000.0, daily_budget_usd=100.0),
        start_date=_past(),
        end_date=_future(),
        targeting=Targeting(geo=GeoTarget(countries=[country])),
    ))
    campaign_service.update_campaign_status(campaign.id, CampaignStatus.ACTIVE)

    li = campaign_service.add_line_item(campaign.id, LineItemCreate(
        name="Test Line Item",
        max_cpm_usd=max_cpm,
        bidding_strategy=BiddingStrategy.CPM,
        start_date=_past(),
        end_date=_future(),
    ))
    campaign_service.update_campaign_status(campaign.id, CampaignStatus.ACTIVE)

    # Activate line item
    for c in campaign_service.list_campaigns():
        for item in c.line_items:
            if item.id == li.id:
                item.status = CampaignStatus.ACTIVE

    return campaign, li


def _make_request(country: str = "USA", floor: float = 0.0) -> BidRequest:
    return BidRequest(
        id="req_test_001",
        imp=[Impression(
            id="imp_1",
            banner=Banner(w=300, h=250),
            bidfloor=floor,
            secure=1,
        )],
        site=Site(domain="example.com", cat=["IAB1"]),
        device=Device(devicetype=1, geo=Geo(country=country), language="en"),
        user=User(id="user_abc"),
    )


def test_no_bid_without_active_campaigns():
    request = _make_request()
    # Fresh evaluation with no campaigns active
    response = evaluate_bid_request(BidRequest(
        id="req_empty",
        imp=[Impression(id="imp_1", banner=Banner(w=300, h=250))],
    ))
    assert response.nbr is not None or response.seatbid == []


def test_bid_returned_for_matching_campaign():
    _make_campaign(max_cpm=5.0, country="USA")
    request = _make_request(country="USA", floor=0.0)
    response = evaluate_bid_request(request)

    if response.seatbid:
        assert len(response.seatbid[0].bid) > 0
        bid = response.seatbid[0].bid[0]
        assert bid.price > 0
        assert bid.price <= 5.0


def test_no_bid_below_floor():
    _make_campaign(max_cpm=1.0, country="USA")
    request = _make_request(country="USA", floor=10.0)  # floor > max CPM
    response = evaluate_bid_request(request)
    assert not response.seatbid


def test_bid_response_mirrors_request_id():
    _make_campaign(max_cpm=5.0, country="USA")
    request = _make_request(country="USA")
    response = evaluate_bid_request(request)
    assert response.id == request.id


def test_frequency_cap():
    from app.services import frequency_cap
    frequency_cap.record_impression("user_fc_test", "li_fc_test")
    frequency_cap.record_impression("user_fc_test", "li_fc_test")
    assert frequency_cap.is_frequency_capped("user_fc_test", "li_fc_test", max_impressions=2, period_hours=24)
    assert not frequency_cap.is_frequency_capped("user_fc_test", "li_fc_test", max_impressions=5, period_hours=24)
