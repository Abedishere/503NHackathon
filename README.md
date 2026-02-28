# Conut AI Operations Agent

An AI-driven Chief of Operations Agent that turns Conut bakery's operational data into actionable business decisions. Built for the AUB AI Engineering Hackathon 2026.

## Business Problem

Conut operates 4 branches selling specialty chimneys, conuts, beverages, and desserts. Operational decisions — product bundling, inventory planning, staffing, expansion, and category growth — need data-driven support. This system provides a unified decision-support API that answers 5 core business objectives, accessible through any messaging platform via OpenClaw integration.

## Five Business Objectives

| # | Objective | Method | Key Output |
|---|-----------|--------|------------|
| 1 | **Combo Optimization** | Apriori association rule mining on customer baskets | Top product bundles ranked by lift/support |
| 2 | **Demand Forecasting** | Exponential smoothing on per-branch monthly sales | 3-month forecasts with confidence bands |
| 3 | **Expansion Feasibility** | Composite branch health scoring (revenue, customers, tax) | Risk-adjusted expansion recommendations |
| 4 | **Shift Staffing** | Demand-to-attendance ratio analysis | Per-branch, per-shift headcount recommendations |
| 5 | **Coffee & Milkshake Growth** | Category performance + cross-sell analysis | Growth strategies with specific action items |

## Architecture

```
User (WhatsApp/Telegram/Slack/Discord)
    → OpenClaw Gateway (loads SKILL.md)
    → FastAPI REST API (5 endpoints)
    → Operations Agent Service Layer
    → Models + Feature Engineering
    → Data Ingestion (9 report-style CSVs)
```

See [docs/architecture.md](docs/architecture.md) for the full system design.

## How to Run

### Prerequisites
- Python 3.10+
- pip

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full data pipeline (ingest → clean → validate → save artifacts)
python scripts/run_pipeline.py

# Run all models and save results
python scripts/train_models.py

# Start the API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Run smoke test
python scripts/demo_smoke_test.py

# Run all tests
pytest tests/ -v
```

### Using Make

```bash
make install     # Install dependencies
make pipeline    # Run data pipeline
make train       # Train models and save results
make api         # Start API server
make test        # Run test suite
make smoke       # Run smoke test
make all         # Full pipeline: install → pipeline → train → test → smoke
```

### Docker

```bash
make docker-build   # Build Docker image
make docker-run     # Run with docker-compose
```

### API Endpoints

Once the server is running:

```bash
# Health check
curl http://localhost:8000/health

# Combo optimization
curl -X POST http://localhost:8000/combo \
  -H "Content-Type: application/json" \
  -d '{"min_support": 0.01, "min_lift": 1.5, "top_n": 10}'

# Demand forecasting
curl -X POST http://localhost:8000/demand \
  -H "Content-Type: application/json" \
  -d '{"branch": "all", "horizon_months": 3}'

# Expansion feasibility
curl -X POST http://localhost:8000/expansion \
  -H "Content-Type: application/json" \
  -d '{"risk_tolerance": "moderate"}'

# Staffing estimation
curl -X POST http://localhost:8000/staffing \
  -H "Content-Type: application/json" \
  -d '{"branch": "all", "period": "next_month"}'

# Growth strategy
curl -X POST http://localhost:8000/growth \
  -H "Content-Type: application/json" \
  -d '{"category": "all"}'
```

All endpoints return a unified JSON response:

```json
{
  "objective": "combo_optimization",
  "scores": [...],
  "rationale": "...",
  "confidence": 0.85,
  "actions": ["..."],
  "data": {...}
}
```

## OpenClaw Integration

This system integrates with [OpenClaw](https://github.com/openclaw/openclaw) so users can query business intelligence from any messaging channel.

### Setup

1. Start the API server: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
2. Install the skill in OpenClaw:
   ```bash
   mkdir -p ~/.openclaw/workspace/skills/conut-ops
   cp skills/conut-ops/SKILL.md ~/.openclaw/workspace/skills/conut-ops/SKILL.md
   ```
3. Set the environment variable:
   ```bash
   export CONUT_API_URL="http://127.0.0.1:8000"
   ```
4. Ask OpenClaw: *"What are the best product combos for Conut?"*

See [docs/openclaw-integration.md](docs/openclaw-integration.md) for the full integration spec including webhook push notifications.

## Key Results

- **Combo**: Classic Chimney + Conut The One + Chimney The One identified as highest-affinity bundle (lift >50x)
- **Demand**: All branches show varying trends; exponential smoothing provides 3-month forecasts with confidence intervals
- **Expansion**: Conut Jnah scores highest (0.67) on health metrics — expansion is feasible at moderate risk tolerance
- **Staffing**: Conut - Tyre and Main Street Coffee are overstaffed evenings; Conut Jnah needs more staff
- **Growth**: Coffee (5% share) and milkshakes (7% share) both have high growth potential via bundling and promotions

## Project Structure

```
├── src/
│   ├── config.py                  # Central configuration
│   ├── data/
│   │   ├── ingest_reports.py      # Per-report parsers (9 CSV formats)
│   │   ├── clean_reports.py       # Cleaning pipeline
│   │   └── validate.py            # QA validation
│   ├── features/                  # Feature engineering per objective
│   ├── models/                    # ML/analytics models per objective
│   ├── services/
│   │   └── operations_agent.py    # Unified service layer
│   ├── api/
│   │   ├── main.py               # FastAPI application
│   │   └── schemas.py            # Pydantic request/response models
│   └── integrations/
│       └── openclaw_tool.py       # OpenClaw skill + webhook client
├── scripts/
│   ├── run_pipeline.py            # Full data pipeline
│   ├── train_models.py            # Run all models
│   ├── generate_recommendations.py # Generate OpenClaw skill
│   └── demo_smoke_test.py         # End-to-end smoke test
├── tests/                         # 30 tests covering all components
├── skills/conut-ops/SKILL.md      # OpenClaw skill definition
├── docker/                        # Dockerfile + docker-compose
├── docs/
│   ├── architecture.md            # System architecture
│   ├── openclaw-integration.md    # Integration specification
│   └── executive_brief.html       # Executive summary (PDF-ready)
├── artifacts/                     # Generated model outputs + cleaned data
├── Conut bakery Scaled Data/      # Raw data (9 CSV files)
├── requirements.txt               # Pinned dependencies
├── pyproject.toml                 # Project metadata
└── Makefile                       # Build automation
```

## Technical Stack

- **Python 3.10+** with pandas, scikit-learn, mlxtend, statsmodels
- **FastAPI** + Pydantic for the REST API
- **mlxtend** Apriori for association rule mining
- **statsmodels** exponential smoothing for demand forecasting
- **OpenClaw** skill-based integration for multi-channel access
- **Docker** for containerized deployment
- **pytest** with 30 tests covering ingestion, models, API, and integration

## Executive Brief

See [docs/executive_brief.html](docs/executive_brief.html) for a 2-page executive summary with findings, recommendations, and impact analysis.

## Contributors
Abdel Rahman El Kouche
Karim Assi
Karl Gerges

---

**AUB AI Engineering Hackathon 2026** | Professor Ammar Mohanna
