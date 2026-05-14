from enum import Enum
from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class BiddingStrategy(str, Enum):
    CPM = "cpm"           # fixed CPM
    DYNAMIC_CPM = "dcpm"  # bid up to max CPM based on targeting score
    CPC = "cpc"           # target CPC (requires conversion tracking)


class DeviceTypeTarget(int, Enum):
    MOBILE = 1
    PC = 2
    TV = 3
    PHONE = 4
    TABLET = 5
    CONNECTED_DEVICE = 6
    SET_TOP_BOX = 7


class GeoTarget(BaseModel):
    countries: list[str] = []    # ISO 3166-1 Alpha-3 e.g. ["USA", "GBR"]
    regions: list[str] = []      # e.g. ["CA", "NY"]
    cities: list[str] = []


class AudienceTarget(BaseModel):
    segment_ids: list[str] = []           # from audience-segmentation-service
    require_all: bool = False             # True=AND, False=OR


class InventoryTarget(BaseModel):
    allowed_domains: list[str] = []
    blocked_domains: list[str] = []
    allowed_iab_categories: list[str] = []
    blocked_iab_categories: list[str] = []
    allowed_placement_types: list[int] = []   # banner, video, native
    require_secure: bool = True


class FrequencyCapRule(BaseModel):
    impressions: int
    period_hours: int    # e.g. 3 imps per 24 hours


class Targeting(BaseModel):
    geo: GeoTarget = GeoTarget()
    device_types: list[DeviceTypeTarget] = []
    audience: AudienceTarget = AudienceTarget()
    inventory: InventoryTarget = InventoryTarget()
    frequency_cap: Optional[FrequencyCapRule] = None
    os: list[str] = []                   # e.g. ["iOS", "Android"]
    languages: list[str] = []            # e.g. ["en", "es"]


class Budget(BaseModel):
    total_budget_usd: float
    daily_budget_usd: Optional[float] = None
    spent_usd: float = 0.0
    daily_spent_usd: float = 0.0
    last_reset_date: Optional[str] = None

    def has_budget(self) -> bool:
        if self.spent_usd >= self.total_budget_usd:
            return False
        if self.daily_budget_usd and self.daily_spent_usd >= self.daily_budget_usd:
            return False
        return True

    def remaining_usd(self) -> float:
        total_remaining = self.total_budget_usd - self.spent_usd
        if self.daily_budget_usd:
            daily_remaining = self.daily_budget_usd - self.daily_spent_usd
            return min(total_remaining, daily_remaining)
        return total_remaining


class LineItem(BaseModel):
    id: str
    campaign_id: str
    name: str
    status: CampaignStatus = CampaignStatus.DRAFT
    bidding_strategy: BiddingStrategy = BiddingStrategy.CPM
    max_cpm_usd: float                   # maximum bid price
    creative_ids: list[str] = []
    targeting: Targeting = Targeting()
    start_date: datetime
    end_date: datetime
    priority: int = 5                    # 1=highest, 10=lowest
    created_at: datetime
    updated_at: datetime


class CampaignCreate(BaseModel):
    name: str
    advertiser_id: str
    budget: Budget
    start_date: datetime
    end_date: datetime
    targeting: Targeting = Targeting()

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class Campaign(BaseModel):
    id: str
    name: str
    advertiser_id: str
    status: CampaignStatus = CampaignStatus.DRAFT
    budget: Budget
    targeting: Targeting
    start_date: datetime
    end_date: datetime
    line_items: list[LineItem] = []
    created_at: datetime
    updated_at: datetime


class LineItemCreate(BaseModel):
    name: str
    bidding_strategy: BiddingStrategy = BiddingStrategy.CPM
    max_cpm_usd: float
    creative_ids: list[str] = []
    targeting: Targeting = Targeting()
    start_date: datetime
    end_date: datetime
    priority: int = 5


def new_campaign_id() -> str:
    return f"cmp_{uuid.uuid4().hex[:16]}"


def new_lineitem_id() -> str:
    return f"li_{uuid.uuid4().hex[:16]}"
