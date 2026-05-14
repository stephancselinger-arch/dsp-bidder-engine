from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import bid, campaigns, win

app = FastAPI(
    title="DSP Bidder Engine",
    description=(
        "OpenRTB 2.6 compliant Demand-Side Platform bidding engine. "
        "Handles real-time bid requests with targeting, frequency capping, "
        "budget pacing, and win/loss notice processing."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bid.router, prefix="/v1")
app.include_router(campaigns.router, prefix="/v1")
app.include_router(win.router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok", "openrtb_version": "2.6"}
