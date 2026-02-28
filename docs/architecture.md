# Architecture Overview

## System Design

```
┌──────────────────────────────────────────────────────────────┐
│  User (WhatsApp / Telegram / Slack / Discord / WebChat)      │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  OpenClaw Gateway (127.0.0.1:18789)                          │
│  ├── Loads SKILL.md (conut-ops skill)                        │
│  └── Executes curl against our API                           │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP POST
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI REST API (0.0.0.0:8000)                             │
│  ├── POST /combo      → Combo Optimization                   │
│  ├── POST /demand     → Demand Forecasting                   │
│  ├── POST /expansion  → Expansion Feasibility                │
│  ├── POST /staffing   → Staffing Estimation                  │
│  ├── POST /growth     → Growth Strategy                      │
│  └── GET  /health     → Health Check                         │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Operations Agent Service Layer                               │
│  (src/services/operations_agent.py)                           │
│  ├── Loads data once on startup                               │
│  ├── Caches cleaned datasets in memory                        │
│  └── Routes requests to objective-specific models             │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Models        │ │ Features     │ │ Data Layer   │
│ combo_opt.    │ │ combo_feat.  │ │ ingest.py    │
│ demand_fc.    │ │ demand_feat. │ │ clean.py     │
│ expansion.    │ │ expansion_f. │ │ validate.py  │
│ staffing.     │ │ staffing_f.  │ │              │
│ growth.       │ │ growth_f.    │ │              │
└──────────────┘ └──────────────┘ └──────┬───────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │ CSV Data Files    │
                              │ (9 report-style)  │
                              └──────────────────┘
```

## Data Flow

1. **Ingestion**: Per-report parsers handle each CSV's unique layout (page headers, section markers, sub-totals)
2. **Cleaning**: Branch name canonicalization, negative-quantity netting, type normalization
3. **Validation**: Row count checks, null rate analysis, branch name verification
4. **Feature Engineering**: Per-objective feature extraction (baskets, time series, health scores, staffing metrics, category performance)
5. **Modeling**: Statistical/ML models per objective (Apriori, exponential smoothing, composite scoring, demand-based staffing, category analysis)
6. **Service Layer**: Unified interface with cached data, deterministic JSON output
7. **API**: FastAPI with Pydantic schemas, strict request/response contracts
8. **Integration**: OpenClaw SKILL.md enables any messaging channel to query the system

## Key Design Decisions

- **Per-report parsers** (not generic CSV reader) because each export has unique layout quirks
- **Net negative quantities per customer** before basket construction to handle cancelled orders
- **Protocol-agnostic core**: analytics logic independent from transport layer
- **Scaled data treated as relative signals**: all analysis uses patterns, ratios, and ranks
- **Exponential smoothing** (not ARIMA/Prophet) given only 5 months of data
- **Stateful service singleton**: data loaded once, cached for fast repeated queries
