"""
OpenRTB 2.6 bid request / response models.
Spec: https://www.iab.com/wp-content/uploads/2022/04/OpenRTB-2-6_FINAL.pdf
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class Banner(BaseModel):
    w: Optional[int] = None
    h: Optional[int] = None
    format: Optional[list[dict]] = None   # [{w, h}]
    btype: Optional[list[int]] = None     # blocked creative types
    battr: Optional[list[int]] = None     # blocked creative attributes
    pos: Optional[int] = None             # ad position (above/below fold)
    api: Optional[list[int]] = None


class Video(BaseModel):
    mimes: list[str] = ["video/mp4"]
    minduration: Optional[int] = None
    maxduration: Optional[int] = None
    protocols: Optional[list[int]] = None  # VAST versions
    w: Optional[int] = None
    h: Optional[int] = None
    linearity: Optional[int] = None        # 1=linear, 2=non-linear
    skip: Optional[int] = None            # 1=skippable
    skipmin: Optional[int] = 0
    skipafter: Optional[int] = None
    placement: Optional[int] = None       # 1=in-stream, 2=in-banner, etc.
    playbackmethod: Optional[list[int]] = None
    delivery: Optional[list[int]] = None
    api: Optional[list[int]] = None


class Native(BaseModel):
    request: str                          # JSON-encoded native request
    ver: Optional[str] = "1.2"
    api: Optional[list[int]] = None
    battr: Optional[list[int]] = None


class Impression(BaseModel):
    id: str
    banner: Optional[Banner] = None
    video: Optional[Video] = None
    native: Optional[Native] = None
    displaymanager: Optional[str] = None
    displaymanagerver: Optional[str] = None
    instl: int = 0                        # 1=interstitial
    tagid: Optional[str] = None
    bidfloor: float = 0.0                 # CPM floor in USD
    bidfloorcur: str = "USD"
    secure: Optional[int] = None          # 1=HTTPS required
    pmp: Optional[dict] = None            # private marketplace deals


class Publisher(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    cat: Optional[list[str]] = None


class Site(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    cat: Optional[list[str]] = None       # IAB content categories
    page: Optional[str] = None
    ref: Optional[str] = None
    publisher: Optional[Publisher] = None
    keywords: Optional[str] = None


class App(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    bundle: Optional[str] = None          # com.example.app
    domain: Optional[str] = None
    storeurl: Optional[str] = None
    cat: Optional[list[str]] = None
    publisher: Optional[Publisher] = None


class Geo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    country: Optional[str] = None         # ISO 3166-1 Alpha-3
    region: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    type: Optional[int] = None            # 1=GPS, 2=IP, 3=user-provided


class Device(BaseModel):
    ua: Optional[str] = None
    geo: Optional[Geo] = None
    ip: Optional[str] = None
    devicetype: Optional[int] = None      # 1=mobile, 2=PC, 3=TV, 4=phone, 5=tablet
    make: Optional[str] = None
    model: Optional[str] = None
    os: Optional[str] = None
    osv: Optional[str] = None
    language: Optional[str] = None
    connectiontype: Optional[int] = None  # 0=unknown, 1=ethernet, 2=wifi, 4=4G, 5=5G


class User(BaseModel):
    id: Optional[str] = None
    buyeruid: Optional[str] = None
    yob: Optional[int] = None             # year of birth
    gender: Optional[str] = None          # M/F/O
    keywords: Optional[str] = None
    data: Optional[list[dict]] = None     # audience segment data


class Regs(BaseModel):
    coppa: Optional[int] = None           # 1=COPPA applies
    gdpr: Optional[int] = None            # 1=GDPR applies (ext)
    us_privacy: Optional[str] = None      # CCPA consent string (ext)
    ext: Optional[dict] = None


# ── Bid Request ───────────────────────────────────────────────────────────────

class BidRequest(BaseModel):
    id: str
    imp: list[Impression]
    site: Optional[Site] = None
    app: Optional[App] = None
    device: Optional[Device] = None
    user: Optional[User] = None
    regs: Optional[Regs] = None
    at: int = 2                           # auction type: 1=first price, 2=second price
    tmax: Optional[int] = 150            # timeout in ms
    wseat: Optional[list[str]] = None    # whitelisted buyer seats
    bseat: Optional[list[str]] = None    # blocked buyer seats
    cur: list[str] = ["USD"]
    bcat: Optional[list[str]] = None     # blocked advertiser categories
    badv: Optional[list[str]] = None     # blocked advertiser domains
    test: int = 0                         # 1=test mode, no billing


# ── Bid Response ──────────────────────────────────────────────────────────────

class Bid(BaseModel):
    id: str
    impid: str                            # matches Impression.id
    price: float                          # CPM bid price
    adid: Optional[str] = None
    nurl: Optional[str] = None            # win notice URL
    burl: Optional[str] = None            # billing notice URL
    lurl: Optional[str] = None            # loss notice URL
    adm: Optional[str] = None            # ad markup
    adomain: Optional[list[str]] = None
    bundle: Optional[str] = None
    iurl: Optional[str] = None           # image URL for content checking
    cid: Optional[str] = None            # campaign ID
    crid: Optional[str] = None           # creative ID
    cat: Optional[list[str]] = None
    attr: Optional[list[int]] = None
    w: Optional[int] = None
    h: Optional[int] = None
    exp: int = 300                        # bid expiry seconds


class SeatBid(BaseModel):
    bid: list[Bid]
    seat: Optional[str] = None
    group: int = 0


class BidResponse(BaseModel):
    id: str                               # mirrors BidRequest.id
    seatbid: list[SeatBid] = []
    bidid: Optional[str] = None
    cur: str = "USD"
    customdata: Optional[str] = None
    nbr: Optional[int] = None            # no-bid reason code


# No-bid reason codes (OpenRTB 2.6 §7.2)
class NoBidReason:
    UNKNOWN = 0
    TECHNICAL_ERROR = 1
    INVALID_REQUEST = 2
    KNOWN_WEB_SPIDER = 3
    SUSPECTED_NON_HUMAN = 4
    PROXY_IP = 5
    UNSUPPORTED_DEVICE = 6
    BLOCKED_PUBLISHER = 7
    UNMATCHED_USER = 8
    DAILY_READER_CAP_MET = 9
    DAILY_DOMAIN_CAP_MET = 10
    NO_ELIGIBLE_CAMPAIGNS = 100
    BELOW_FLOOR_PRICE = 101
    FREQUENCY_CAPPED = 102
    BUDGET_EXHAUSTED = 103
