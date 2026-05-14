"""
Evaluates whether a bid request matches a line item's targeting criteria.
Returns a targeting score (0.0–1.0) used to scale dynamic CPM bids.
"""

from app.models.openrtb import BidRequest, Impression
from app.models.campaign import LineItem, Targeting


def _score_geo(targeting: Targeting, request: BidRequest) -> tuple[bool, float]:
    geo_t = targeting.geo
    if not any([geo_t.countries, geo_t.regions, geo_t.cities]):
        return True, 1.0

    device_geo = request.device.geo if request.device else None
    if not device_geo:
        return False, 0.0

    if geo_t.countries and device_geo.country:
        if device_geo.country.upper() not in [c.upper() for c in geo_t.countries]:
            return False, 0.0

    if geo_t.regions and device_geo.region:
        if device_geo.region not in geo_t.regions:
            return False, 0.5   # country matched, region missed — partial

    if geo_t.cities and device_geo.city:
        if device_geo.city not in geo_t.cities:
            return True, 0.8    # region matched, city missed — still ok

    return True, 1.0


def _score_device(targeting: Targeting, request: BidRequest) -> tuple[bool, float]:
    if not targeting.device_types:
        return True, 1.0
    if not request.device or request.device.devicetype is None:
        return False, 0.0
    if request.device.devicetype in [dt.value for dt in targeting.device_types]:
        return True, 1.0
    return False, 0.0


def _score_inventory(targeting: Targeting, request: BidRequest, imp: Impression) -> tuple[bool, float]:
    inv = targeting.inventory

    domain = None
    if request.site:
        domain = request.site.domain
    elif request.app:
        domain = request.app.domain

    if inv.blocked_domains and domain and domain in inv.blocked_domains:
        return False, 0.0

    if inv.allowed_domains and domain and domain not in inv.allowed_domains:
        return False, 0.0

    site_cats = []
    if request.site and request.site.cat:
        site_cats = request.site.cat
    elif request.app and request.app.cat:
        site_cats = request.app.cat

    if inv.blocked_iab_categories and any(c in inv.blocked_iab_categories for c in site_cats):
        return False, 0.0

    if inv.require_secure and imp.secure != 1:
        return False, 0.0

    return True, 1.0


def _score_language(targeting: Targeting, request: BidRequest) -> tuple[bool, float]:
    if not targeting.languages:
        return True, 1.0
    if not request.device or not request.device.language:
        return True, 0.8   # unknown language — allow with reduced score
    if request.device.language in targeting.languages:
        return True, 1.0
    return False, 0.0


def _score_os(targeting: Targeting, request: BidRequest) -> tuple[bool, float]:
    if not targeting.os:
        return True, 1.0
    if not request.device or not request.device.os:
        return True, 0.8
    if request.device.os in targeting.os:
        return True, 1.0
    return False, 0.0


def evaluate_targeting(line_item: LineItem, request: BidRequest, imp: Impression) -> tuple[bool, float]:
    """
    Returns (eligible, score).
    eligible=False means no bid. score scales the dynamic CPM.
    """
    targeting = line_item.targeting

    checks = [
        _score_geo(targeting, request),
        _score_device(targeting, request),
        _score_inventory(targeting, request, imp),
        _score_language(targeting, request),
        _score_os(targeting, request),
    ]

    for eligible, _ in checks:
        if not eligible:
            return False, 0.0

    scores = [score for _, score in checks]
    composite_score = sum(scores) / len(scores)
    return True, composite_score
