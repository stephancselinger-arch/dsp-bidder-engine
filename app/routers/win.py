from fastapi import APIRouter, Query
from app.services.bid_evaluator import handle_win_notice

router = APIRouter(prefix="/win", tags=["Win Notices"])


@router.get("/win")
def win_notice(
    bid: str = Query(...),
    li: str = Query(...),
    price: float = Query(..., alias="price"),
    uid: str = Query(None),
):
    """
    Win notice endpoint — called by the exchange when we win an auction.
    Records spend and frequency impression for the winning user.
    """
    handle_win_notice(bid_id=bid, line_item_id=li, clearing_price=price, user_id=uid)
    return {"status": "recorded"}


@router.get("/loss")
def loss_notice(bid: str = Query(...), reason: int = Query(None)):
    """Loss notice endpoint — logged for reporting (no action needed)."""
    return {"status": "noted", "bid": bid, "reason": reason}
