"""
Core DSP bid evaluation engine.

For each incoming OpenRTB bid request:
  1. Iterate active campaigns + line items
  2. Check budget, flight dates, targeting, frequency caps
  3. Calculate bid price (CPM or dynamic CPM scaled by targeting score)
  4. Apply pacing
  5. Return highest eligible bid per impression
"""

import uuid
from datetime import datetime, timezone

from app.models.openrtb import (
    BidRequest, BidResponse, SeatBid, Bid, Impression, NoBidReason
)
from app.models.campaign import Campaign, LineItem, BiddingStrategy
from app.services import campaign_service, frequency_cap, pacing
from app.services.targeting import evaluate_targeting

SEAT_ID = "dsp-bidder-01"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _calculate_bid_price(
    line_item: LineItem,
    campaign: Campaign,
    targeting_score: float,
    imp: Impression,
) -> float:
    base = line_item.max_cpm_usd

    if line_item.bidding_strategy == BiddingStrategy.DYNAMIC_CPM:
        base = base * targeting_score

    # Never bid below floor
    if base < imp.bidfloor:
        return 0.0

    # Apply pacing throttle
    paced = pacing.pace_bid(campaign, base)
    return round(paced, 4)


def _select_creative(line_item: LineItem) -> str:
    """Round-robin creative selection."""
    if not line_item.creative_ids:
        return "default_creative"
    idx = hash(line_item.id + str(_now().minute)) % len(line_item.creative_ids)
    return line_item.creative_ids[idx]


def _build_win_notice_url(bid_id: str, line_item_id: str) -> str:
    return f"https://win.dsp-bidder.internal/win?bid={bid_id}&li={line_item_id}&price=${{AUCTION_PRICE}}"


def _build_loss_notice_url(bid_id: str) -> str:
    return f"https://win.dsp-bidder.internal/loss?bid={bid_id}&reason=${{AUCTION_LOSS}}"


def evaluate_bid_request(request: BidRequest) -> BidResponse:
    active_pairs = campaign_service.get_active_line_items()

    if not active_pairs:
        return BidResponse(id=request.id, nbr=NoBidReason.NO_ELIGIBLE_CAMPAIGNS)

    all_seat_bids: list[Bid] = []

    for imp in request.imp:
        best_bid: tuple[float, Bid] | None = None

        for campaign, line_item in active_pairs:
            # Budget check
            if not pacing.has_budget(campaign):
                continue

            # Targeting evaluation
            eligible, targeting_score = evaluate_targeting(line_item, request, imp)
            if not eligible:
                continue

            # Frequency cap check
            user_id = request.user.id if request.user else None
            if user_id and line_item.targeting.frequency_cap:
                fc = line_item.targeting.frequency_cap
                if frequency_cap.is_frequency_capped(user_id, line_item.id, fc.impressions, fc.period_hours):
                    continue

            # Price calculation
            bid_price = _calculate_bid_price(line_item, campaign, targeting_score, imp)
            if bid_price <= 0:
                continue

            creative_id = _select_creative(line_item)
            bid_id = f"bid_{uuid.uuid4().hex[:12]}"

            bid = Bid(
                id=bid_id,
                impid=imp.id,
                price=bid_price,
                adid=creative_id,
                cid=campaign.id,
                crid=creative_id,
                adomain=[],
                nurl=_build_win_notice_url(bid_id, line_item.id),
                lurl=_build_loss_notice_url(bid_id),
            )

            if best_bid is None or bid_price > best_bid[0]:
                best_bid = (bid_price, bid)

        if best_bid:
            all_seat_bids.append(best_bid[1])

    if not all_seat_bids:
        return BidResponse(id=request.id, nbr=NoBidReason.NO_ELIGIBLE_CAMPAIGNS)

    return BidResponse(
        id=request.id,
        bidid=f"resp_{uuid.uuid4().hex[:8]}",
        seatbid=[SeatBid(bid=all_seat_bids, seat=SEAT_ID)],
        cur="USD",
    )


def handle_win_notice(bid_id: str, line_item_id: str, clearing_price: float, user_id: str | None) -> None:
    """Called when we win an auction. Record spend and frequency."""
    pacing.record_spend.__doc__  # lazy import guard

    # Find the campaign for this line item
    for campaign, li in campaign_service.get_active_line_items():
        if li.id == line_item_id:
            pacing.record_spend(campaign.id, clearing_price)
            break

    if user_id:
        frequency_cap.record_impression(user_id, line_item_id)
