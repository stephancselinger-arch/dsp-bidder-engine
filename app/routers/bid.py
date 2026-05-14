from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models.openrtb import BidRequest, BidResponse
from app.services.bid_evaluator import evaluate_bid_request

router = APIRouter(prefix="/bid", tags=["Bidding"])


@router.post("/request", response_model=BidResponse)
async def bid_request(payload: BidRequest):
    """
    OpenRTB 2.6 bid endpoint.
    Returns HTTP 200 with a BidResponse (may contain zero seatbids = no-bid).
    Returns HTTP 204 for explicit no-bid when no campaigns are active.
    """
    response = evaluate_bid_request(payload)

    if not response.seatbid:
        # OpenRTB spec: HTTP 204 is a valid no-bid response
        return JSONResponse(status_code=204, content=None)

    return response
