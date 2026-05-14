import pytest
from datetime import datetime, timezone, timedelta

from app.models.openrtb import BidRequest, Impression, Banner, Device, Geo, Site
from app.models.campaign import (
    LineItem, Targeting, GeoTarget, InventoryTarget,
    CampaignStatus, BiddingStrategy,
)
from app.services.targeting import evaluate_targeting


def _make_line_item(targeting: Targeting) -> LineItem:
    now = datetime.now(timezone.utc)
    return LineItem(
        id="li_test",
        campaign_id="cmp_test",
        name="Test LI",
        status=CampaignStatus.ACTIVE,
        bidding_strategy=BiddingStrategy.CPM,
        max_cpm_usd=5.0,
        targeting=targeting,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )


def _make_request(country="USA", domain="example.com", device_type=1) -> tuple[BidRequest, Impression]:
    imp = Impression(id="imp_1", banner=Banner(w=300, h=250), secure=1)
    req = BidRequest(
        id="req_1",
        imp=[imp],
        site=Site(domain=domain, cat=["IAB1"]),
        device=Device(devicetype=device_type, geo=Geo(country=country), language="en"),
    )
    return req, imp


def test_no_targeting_always_matches():
    li = _make_line_item(Targeting())
    req, imp = _make_request()
    eligible, score = evaluate_targeting(li, req, imp)
    assert eligible
    assert score > 0


def test_geo_country_match():
    li = _make_line_item(Targeting(geo=GeoTarget(countries=["USA"])))
    req, imp = _make_request(country="USA")
    eligible, score = evaluate_targeting(li, req, imp)
    assert eligible


def test_geo_country_mismatch():
    li = _make_line_item(Targeting(geo=GeoTarget(countries=["GBR"])))
    req, imp = _make_request(country="USA")
    eligible, score = evaluate_targeting(li, req, imp)
    assert not eligible


def test_blocked_domain():
    li = _make_line_item(Targeting(
        inventory=InventoryTarget(blocked_domains=["badsite.com"])
    ))
    req, imp = _make_request(domain="badsite.com")
    eligible, score = evaluate_targeting(li, req, imp)
    assert not eligible


def test_score_between_0_and_1():
    li = _make_line_item(Targeting(geo=GeoTarget(countries=["USA"])))
    req, imp = _make_request(country="USA")
    eligible, score = evaluate_targeting(li, req, imp)
    assert eligible
    assert 0.0 <= score <= 1.0
