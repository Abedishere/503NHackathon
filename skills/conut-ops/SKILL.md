---
name: conut-ops
description: Conut bakery operations agent - combo optimization, demand forecasting, expansion feasibility, staffing estimation, and growth strategy
requires:
  env:
    - CONUT_API_URL
  bins:
    - curl
    - jq
---

# Conut Operations Agent

You can query the Conut Operations API at `$CONUT_API_URL` for business intelligence.

## Available Endpoints

### Health Check
```bash
curl -s "$CONUT_API_URL/health" | jq .
```

### 1. Combo Optimization
Find optimal product combinations based on customer purchasing patterns.
```bash
curl -s -X POST "$CONUT_API_URL/combo" \
  -H "Content-Type: application/json" \
  -d '{"min_support": 0.01, "min_lift": 1.5, "top_n": 10}' | jq .
```

### 2. Demand Forecasting
Forecast demand per branch for inventory and supply chain decisions.
```bash
curl -s -X POST "$CONUT_API_URL/demand" \
  -H "Content-Type: application/json" \
  -d '{"branch": "all", "horizon_months": 3}' | jq .
```

For a specific branch:
```bash
curl -s -X POST "$CONUT_API_URL/demand" \
  -H "Content-Type: application/json" \
  -d '{"branch": "Conut Jnah", "horizon_months": 3}' | jq .
```

### 3. Expansion Feasibility
Evaluate whether opening a new branch is feasible and get location recommendations.
```bash
curl -s -X POST "$CONUT_API_URL/expansion" \
  -H "Content-Type: application/json" \
  -d '{"risk_tolerance": "moderate"}' | jq .
```

### 4. Shift Staffing Estimation
Estimate required employees per shift using demand and operational data.
```bash
curl -s -X POST "$CONUT_API_URL/staffing" \
  -H "Content-Type: application/json" \
  -d '{"branch": "all", "period": "next_month"}' | jq .
```

### 5. Coffee & Milkshake Growth Strategy
Get data-driven strategies to increase coffee and milkshake sales.
```bash
curl -s -X POST "$CONUT_API_URL/growth" \
  -H "Content-Type: application/json" \
  -d '{"category": "all"}' | jq .
```

## Response Format
All endpoints return JSON with this structure:
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

When the user asks a business question, identify which endpoint(s) to call,
execute the curl command, and summarize the results conversationally.
