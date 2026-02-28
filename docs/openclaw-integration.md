# OpenClaw Integration Specification

> Concrete contract for connecting our Conut Operations Agent (FastAPI) with OpenClaw.

---

## 1. Architecture Overview

OpenClaw is a single-user, local-first personal AI assistant. Its **Gateway** daemon
runs on the user's machine (default `127.0.0.1:18789`) and manages all messaging
channels (WhatsApp, Telegram, Slack, Discord, etc.).

There are **two integration surfaces** relevant to us:

| Direction | Mechanism | Purpose |
|-----------|-----------|---------|
| **External -> OpenClaw** | Inbound webhooks (`POST /hooks/*`) | Our service pushes alerts/events to the user's agent |
| **OpenClaw -> External** | Skills (SKILL.md with curl/shell) | The agent calls our FastAPI endpoints on demand |

The primary integration path is **OpenClaw calling our service via a Skill**.
The user asks a question in any channel; the agent loads the skill and executes
HTTP calls against our FastAPI API. Optionally, our service can also push
notifications back into OpenClaw via the webhook endpoints.

```
User (WhatsApp/Telegram/etc.)
    |
    v
OpenClaw Gateway (127.0.0.1:18789)
    |
    |--- loads SKILL.md (conut-ops skill)
    |--- agent executes: curl POST http://<our-api>/combo ...
    |
    v
Our FastAPI Service (e.g., 127.0.0.1:8000)
    |
    |--- runs analytics pipeline
    |--- returns JSON response
    |
    v
OpenClaw agent formats answer -> sends to user's channel
```

---

## 2. Integration Path A: OpenClaw Skill (Agent Calls Our API)

This is the **primary integration**. We write a `SKILL.md` file that teaches the
OpenClaw agent how to call our FastAPI endpoints.

### 2.1 Skill File Location

Place the skill folder at one of:
- `~/.openclaw/workspace/skills/conut-ops/SKILL.md` (workspace scope, per-user)
- `~/.openclaw/skills/conut-ops/SKILL.md` (managed scope)

### 2.2 SKILL.md Contents

The skill now covers **12 endpoints** — 5 model endpoints (AI-driven analysis) and 6 EDA data endpoints (pre-computed dashboard tables) plus health.

```markdown
---
name: conut-ops
description: Conut bakery operations agent - combo optimization, demand forecasting, expansion feasibility, staffing estimation, growth strategy, and live EDA data queries
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
  -d '{"branch": "Branch Name", "horizon_months": 3}' | jq .
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
```

### 2.3 Environment Configuration

The user must set the environment variable in their OpenClaw config
(`~/.openclaw/openclaw.json` or `.env`):

```json5
{
  skills: {
    entries: {
      "conut-ops": {
        env: {
          CONUT_API_URL: "http://127.0.0.1:8000"
        }
      }
    }
  }
}
```

Or export it:
```bash
export CONUT_API_URL="http://127.0.0.1:8000"
```

### 2.4 How Execution Works

1. User asks: "What are the best product combos?" (via any channel)
2. OpenClaw agent scans installed skills by name/description
3. Agent loads `conut-ops/SKILL.md` into its context
4. Agent executes: `curl -s -X POST "$CONUT_API_URL/combo" ...`
5. Agent receives JSON response
6. Agent formats a human-readable summary
7. Summary is sent back to the user's channel

---

## 3. Integration Path B: Inbound Webhooks (Our Service Pushes to OpenClaw)

Use this for **proactive notifications** (e.g., "demand spike detected",
"staffing shortage alert").

### 3.1 OpenClaw Webhook Configuration

The user enables webhooks in `~/.openclaw/openclaw.json`:

```json5
{
  hooks: {
    enabled: true,
    token: "a-long-random-secret",
    path: "/hooks",
    allowedAgentIds: ["hooks", "main"]
  }
}
```

### 3.2 Authentication

All webhook requests must include the token. Two methods:

```
Authorization: Bearer <token>
```
or
```
x-openclaw-token: <token>
```

Query-string tokens (`?token=...`) are **rejected** with HTTP 400.

### 3.3 Webhook Endpoints

#### POST /hooks/wake

Enqueues a system event for the main session. Use for simple notifications.

**Request:**
```json
{
  "text": "Conut Alert: Demand spike detected at Downtown branch - 40% above forecast",
  "mode": "now"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | - | Event description the agent receives |
| `mode` | string | No | `"now"` | `"now"` or `"next-heartbeat"` |

**Response:** HTTP 200

#### POST /hooks/agent

Runs an isolated agent turn and delivers the response to a channel. Use for
richer interactions where you want the agent to process and respond.

**Request:**
```json
{
  "message": "A demand spike was detected at the Downtown branch. Current demand is 40% above forecast. Summarize the situation and recommend staffing adjustments.",
  "name": "Conut-Ops",
  "agentId": "hooks",
  "wakeMode": "now",
  "deliver": true,
  "channel": "last",
  "timeoutSeconds": 120
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `message` | string | Yes | - | Prompt/message for the agent |
| `name` | string | No | - | Human-readable label (e.g., "Conut-Ops") |
| `agentId` | string | No | default agent | Route to a specific agent |
| `sessionKey` | string | No | - | Session ID (needs `allowRequestSessionKey=true`) |
| `wakeMode` | string | No | `"now"` | `"now"` or `"next-heartbeat"` |
| `deliver` | boolean | No | `true` | Send response to messaging channel |
| `channel` | string | No | `"last"` | Target channel: `last`, `whatsapp`, `telegram`, `discord`, `slack`, etc. |
| `to` | string | No | last recipient | Recipient ID |
| `model` | string | No | default | Model override |
| `thinking` | string | No | - | `"low"`, `"medium"`, or `"high"` |
| `timeoutSeconds` | number | No | - | Max run duration in seconds |

**Response:** HTTP 202 (async, agent run started)

### 3.4 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | `/hooks/wake` success |
| 202 | `/hooks/agent` async started |
| 400 | Invalid payload or query-string token |
| 401 | Authentication failure |
| 413 | Oversized payload |
| 429 | Rate limited (check `Retry-After` header) |

### 3.5 Python Client for Pushing to OpenClaw

```python
"""src/integrations/openclaw_webhook.py"""
import httpx
from typing import Optional, Literal


class OpenClawWebhook:
    """Client for pushing notifications to OpenClaw webhooks."""

    def __init__(self, gateway_url: str = "http://127.0.0.1:18789", token: str = ""):
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30.0,
        )

    async def wake(self, text: str, mode: str = "now") -> int:
        """Send a simple wake event to OpenClaw."""
        resp = await self._client.post(
            f"{self.gateway_url}/hooks/wake",
            json={"text": text, "mode": mode},
        )
        resp.raise_for_status()
        return resp.status_code

    async def agent(
        self,
        message: str,
        name: str = "Conut-Ops",
        channel: Optional[str] = "last",
        deliver: bool = True,
        timeout_seconds: int = 120,
    ) -> int:
        """Trigger an agent turn with a message and deliver response to channel."""
        resp = await self._client.post(
            f"{self.gateway_url}/hooks/agent",
            json={
                "message": message,
                "name": name,
                "wakeMode": "now",
                "deliver": deliver,
                "channel": channel,
                "timeoutSeconds": timeout_seconds,
            },
        )
        resp.raise_for_status()
        return resp.status_code

    async def close(self):
        await self._client.aclose()
```

---

## 4. Our FastAPI Service Contract

These are the endpoints our service must expose for the OpenClaw skill to call.

### 4.1 Base Configuration

```
Host: 127.0.0.1:8000  (or configurable)
Content-Type: application/json
```

No authentication is needed if running locally on the same machine as OpenClaw.
If exposed over a network, add a Bearer token check.

### 4.2 Endpoints

#### GET /health
```json
{"status": "ok", "version": "1.0.0"}
```

---

#### EDA Data Endpoints (GET, pre-computed tables)

These expose the same data shown in the Streamlit dashboard (`eda/app/`).
All accept `?branch=<name>` to filter by branch.

| Endpoint | Source CSV | Rows |
|---|---|---|
| `GET /eda/branch-kpis` | `branch_kpis.csv` | 4 |
| `GET /eda/combos?top_n=N` | `combo_pairs_scored_all_branches.csv` | 267 |
| `GET /eda/growth` | `growth_metrics_all_branches.csv` | 4 |
| `GET /eda/channels` | `channel_shares.csv` | 7 |
| `GET /eda/staffing` | `attendance_daily_hours.csv` | 87 |
| `GET /eda/customers` | `customer_rfm_lite.csv` | 508 |

**EDA Response shape:**
```json
{"table": "branch_kpis", "branch": "all", "rows": [...], "count": 4}
```

**Note:** EDA tables are generated by `python -m eda.scripts.run_eda` and cached to `eda/outputs/tables/`. The API endpoints serve these CSVs directly; no ML inference is triggered.

---

#### POST /combo
**Request:**
```json
{
  "min_support": 0.01,
  "min_lift": 1.5,
  "top_n": 10
}
```
All fields optional with defaults shown above.

**Response:**
```json
{
  "objective": "combo_optimization",
  "scores": [
    {"items": ["Croissant", "Latte"], "support": 0.15, "confidence": 0.72, "lift": 3.2},
    {"items": ["Muffin", "Cappuccino"], "support": 0.12, "confidence": 0.68, "lift": 2.8}
  ],
  "rationale": "Top combos identified from 12,000+ transactions using association rule mining.",
  "confidence": 0.85,
  "actions": [
    "Bundle Croissant + Latte as a breakfast combo at 10% discount",
    "Place Muffin near Cappuccino station for impulse purchase"
  ],
  "data": {"total_transactions": 12345, "unique_items": 87, "rules_found": 42}
}
```

#### POST /demand
**Request:**
```json
{
  "branch": "all",
  "horizon_months": 3
}
```

**Response:**
```json
{
  "objective": "demand_forecasting",
  "scores": [
    {
      "branch": "Downtown",
      "forecast": [
        {"month": "2026-03", "predicted": 1520, "lower": 1380, "upper": 1660},
        {"month": "2026-04", "predicted": 1610, "lower": 1450, "upper": 1770}
      ],
      "trend": "increasing"
    }
  ],
  "rationale": "Exponential smoothing on 5-month branch sales history.",
  "confidence": 0.72,
  "actions": ["Increase Downtown inventory by 15% for March"],
  "data": {"model": "exponential_smoothing", "training_months": 5}
}
```

#### POST /expansion
**Request:**
```json
{
  "risk_tolerance": "moderate"
}
```

**Response:**
```json
{
  "objective": "expansion_feasibility",
  "scores": [
    {"location": "Area X", "feasibility_score": 0.82, "risk_level": "low", "roi_estimate": "positive"},
    {"location": "Area Y", "feasibility_score": 0.65, "risk_level": "moderate", "roi_estimate": "uncertain"}
  ],
  "rationale": "Scored using branch health metrics, customer density, and revenue trends.",
  "confidence": 0.68,
  "actions": ["Prioritize Area X for pilot expansion", "Conduct foot-traffic study for Area Y"],
  "data": {"branches_analyzed": 5, "metrics_used": ["revenue_trend", "customer_frequency", "tax_contribution"]}
}
```

#### POST /staffing
**Request:**
```json
{
  "branch": "all",
  "period": "next_month"
}
```

**Response:**
```json
{
  "objective": "staffing_estimation",
  "scores": [
    {
      "branch": "Downtown",
      "shifts": [
        {"shift": "morning", "current_staff": 3, "recommended_staff": 4, "gap": 1},
        {"shift": "evening", "current_staff": 4, "recommended_staff": 3, "gap": -1}
      ]
    }
  ],
  "rationale": "Staffing ratios computed from demand forecast vs. actual attendance hours.",
  "confidence": 0.75,
  "actions": ["Hire 1 additional morning staff at Downtown", "Reduce evening overstaffing"],
  "data": {"attendance_records": 2500, "demand_correlation": 0.83}
}
```

#### POST /growth
**Request:**
```json
{
  "category": "all"
}
```

**Response:**
```json
{
  "objective": "growth_strategy",
  "scores": [
    {"category": "coffee", "current_share": 0.22, "growth_potential": "high"},
    {"category": "milkshake", "current_share": 0.08, "growth_potential": "moderate"}
  ],
  "rationale": "Cross-referenced item sales with combo affinities and repeat purchase rates.",
  "confidence": 0.70,
  "actions": [
    "Launch coffee loyalty program targeting repeat customers",
    "Bundle milkshakes with top-selling pastry items",
    "Test afternoon milkshake promotion (2-5 PM discount)"
  ],
  "data": {"items_analyzed": 15, "customer_segments": 4}
}
```

### 4.3 Unified Response Schema (Pydantic)

```python
from pydantic import BaseModel
from typing import Any, List, Optional


class OperationsResponse(BaseModel):
    objective: str
    scores: List[Any]
    rationale: str
    confidence: float
    actions: List[str]
    data: Optional[dict] = None
```

---

## 5. Full Integration Checklist

### For Demo Day

1. **Start our FastAPI service:**
   ```bash
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Install the skill in OpenClaw:**
   ```bash
   mkdir -p ~/.openclaw/workspace/skills/conut-ops
   cp skills/conut-ops/SKILL.md ~/.openclaw/workspace/skills/conut-ops/SKILL.md
   ```

3. **Set the environment variable:**
   ```bash
   export CONUT_API_URL="http://127.0.0.1:8000"
   ```
   Or add to OpenClaw config:
   ```json5
   { skills: { entries: { "conut-ops": { env: { CONUT_API_URL: "http://127.0.0.1:8000" } } } } }
   ```

4. **Test via OpenClaw:**
   - Open any connected channel (WhatsApp, Telegram, etc.)
   - Ask: "What are the best product combos for Conut?"
   - Agent loads the conut-ops skill, calls `POST /combo`, returns formatted answer

5. **(Optional) Enable webhook notifications:**
   - Configure `hooks.enabled: true` and `hooks.token` in OpenClaw
   - Our service pushes alerts via `POST /hooks/wake` or `/hooks/agent`

### Verification Commands

```bash
# Test our API directly
curl -s http://127.0.0.1:8000/health | jq .

# Test combo endpoint
curl -s -X POST http://127.0.0.1:8000/combo \
  -H "Content-Type: application/json" \
  -d '{"top_n": 5}' | jq .

# Test webhook push to OpenClaw (if configured)
curl -X POST http://127.0.0.1:18789/hooks/wake \
  -H 'Authorization: Bearer YOUR_HOOK_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Conut test alert","mode":"now"}'
```

---

## 6. Security Notes

- OpenClaw Gateway binds to `127.0.0.1` by default (loopback only).
- For remote access, OpenClaw recommends Tailscale or SSH tunnels -- do not expose port 18789 to the internet.
- Webhook tokens should be long random strings, not reused from other credentials.
- Hook payloads are treated as untrusted by OpenClaw and wrapped with safety boundaries by default.
- Our FastAPI service needs no auth when co-located on the same machine. Add Bearer token middleware if exposed over a network.

---

## Sources

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Webhooks Documentation](https://docs.openclaw.ai/automation/webhook)
- [OpenClaw Skills Documentation](https://docs.openclaw.ai/tools/skills)
- [OpenClaw Architecture](https://docs.openclaw.ai/concepts/architecture)
- [OpenClaw Custom API Integration Guide (LumaDock)](https://lumadock.com/tutorials/openclaw-custom-api-integration-guide)
- [OpenClaw Web Tools](https://docs.openclaw.ai/tools/web)
- [OpenClaw Plugin API](https://docs.openclaw.ai/tools/plugin)
