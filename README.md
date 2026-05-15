# DSP Bidder Engine

OpenRTB 2.6 compliant Demand-Side Platform (DSP) real-time bidding engine. Handles bid requests from exchanges and SSPs, evaluates active campaigns, applies targeting and frequency capping, paces budgets, and returns valid bid responses — all within exchange timeout windows (≤150ms).

## Features

- **OpenRTB 2.6 Compliance** — full BidRequest/BidResponse spec with proper no-bid codes
- **Multi-format Support** — banner, video, and native impressions
- **Targeting Engine** — geo (country/region/city), device type, OS, language, domain allow/blocklists, IAB category filters
- **Frequency Capping** — per-user, per-line-item rolling window caps (Redis-ready)
- **Budget Pacing** — total + daily budgets with smooth time-of-day pacing to avoid front-loading spend
- **Dynamic CPM Bidding** — scales bid price by targeting match score
- **Win/Loss Notices** — NURL/LURL handlers that record spend and impression frequency
- **Campaign Management** — full campaign + line item CRUD with flight date controls

## Architecture

```
Exchange/SSP
    │  POST /v1/bid/request (OpenRTB 2.6)
    ▼
Bid Evaluator
    ├── Campaign Service   (active campaigns + line items)
    ├── Targeting Engine   (geo, device, inventory checks)
    ├── Frequency Cap      (rolling window per user)
    └── Pacing Engine      (budget + daily spend throttle)
    │
    ▼  BidResponse (winning bid)
Exchange runs auction → Win Notice → NURL callback
                                         │
                                    record_spend()
                                    record_impression()
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload
```

API docs: http://localhost:8002/docs

## Docker

```bash
docker compose up
```

## API Reference

### Bidding

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/bid/request` | OpenRTB 2.6 bid endpoint |
| `GET` | `/v1/win/win` | Win notice handler (NURL) |
| `GET` | `/v1/win/loss` | Loss notice handler (LURL) |

### Campaigns

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/campaigns/` | Create a campaign |
| `GET` | `/v1/campaigns/` | List campaigns |
| `GET` | `/v1/campaigns/{id}` | Get campaign details |
| `PATCH` | `/v1/campaigns/{id}/status` | Activate / pause / archive |
| `POST` | `/v1/campaigns/{id}/line-items` | Add a line item |

## Example: OpenRTB Bid Request

```json
POST /v1/bid/request
{
  "id": "req_abc123",
  "imp": [{
    "id": "1",
    "banner": {"w": 300, "h": 250},
    "bidfloor": 1.50,
    "secure": 1
  }],
  "site": {
    "domain": "publisher.com",
    "cat": ["IAB1", "IAB19"]
  },
  "device": {
    "ua": "Mozilla/5.0...",
    "ip": "12.34.56.78",
    "devicetype": 1,
    "geo": {"country": "USA", "region": "CA"}
  },
  "user": {"id": "usr_xyz789"},
  "tmax": 150
}
```

Response (win):
```json
{
  "id": "req_abc123",
  "seatbid": [{
    "bid": [{
      "id": "bid_f3a2b1c4d5e6",
      "impid": "1",
      "price": 3.45,
      "crid": "cr_abc123",
      "nurl": "https://win.dsp-bidder.internal/win?bid=...&price=${AUCTION_PRICE}"
    }],
    "seat": "dsp-bidder-01"
  }],
  "cur": "USD"
}
```

## Example: Create a Campaign

```json
POST /v1/campaigns/
{
  "name": "Q3 Brand Awareness",
  "advertiser_id": "adv_abc123",
  "budget": {
    "total_budget_usd": 50000,
    "daily_budget_usd": 2000
  },
  "start_date": "2026-06-01T00:00:00Z",
  "end_date": "2026-09-30T23:59:59Z",
  "targeting": {
    "geo": {"countries": ["USA", "CAN"]},
    "device_types": [1, 4, 5],
    "inventory": {
      "blocked_domains": ["lowquality.com"],
      "require_secure": true
    }
  }
}
```

## Running Tests

```bash
pytest tests/ -v
```

## Production Considerations

| Component | Dev (current) | Production |
|-----------|--------------|------------|
| Frequency cap store | In-memory dict | Redis (INCR + EXPIRE) |
| Spend tracking | In-memory dict | PostgreSQL ledger |
| Campaign store | In-memory dict | PostgreSQL + Redis cache |
| Bid latency | ~5ms | Target ≤30ms with Redis |

## Tech Stack

- **FastAPI** — async REST, handles concurrent bid requests
- **Pydantic v2** — OpenRTB model validation
- Python 3.12+

<!-- Last updated: 2026-05-14 -->

<!-- Last updated: 2026-05-15 -->
