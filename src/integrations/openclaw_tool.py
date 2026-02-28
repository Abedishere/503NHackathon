"""OpenClaw integration — Skill file generator and webhook client (mandatory).

Two integration paths:
  A) Skill: OpenClaw agent loads SKILL.md, calls our FastAPI endpoints to execute
     operational queries (demand prediction, staffing, combos, expansion, growth).
  B) Webhook: Our service pushes alerts/results to OpenClaw gateway.
"""

import httpx
from pathlib import Path
from typing import Optional
from src.config import OPENCLAW_GATEWAY_URL, OPENCLAW_HOOK_TOKEN
from src.utils.logging import get_logger

log = get_logger(__name__)

SKILL_MD = '''---
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
curl -s -X POST "$CONUT_API_URL/combo" \\
  -H "Content-Type: application/json" \\
  -d \'{"min_support": 0.01, "min_lift": 1.5, "top_n": 10}\' | jq .
```

### 2. Demand Forecasting
Forecast demand per branch for inventory and supply chain decisions.
```bash
curl -s -X POST "$CONUT_API_URL/demand" \\
  -H "Content-Type: application/json" \\
  -d \'{"branch": "all", "horizon_months": 3}\' | jq .
```

For a specific branch:
```bash
curl -s -X POST "$CONUT_API_URL/demand" \\
  -H "Content-Type: application/json" \\
  -d \'{"branch": "Conut Jnah", "horizon_months": 3}\' | jq .
```

### 3. Expansion Feasibility
Evaluate whether opening a new branch is feasible and get location recommendations.
```bash
curl -s -X POST "$CONUT_API_URL/expansion" \\
  -H "Content-Type: application/json" \\
  -d \'{"risk_tolerance": "moderate"}\' | jq .
```

### 4. Shift Staffing Estimation
Estimate required employees per shift using demand and operational data.
```bash
curl -s -X POST "$CONUT_API_URL/staffing" \\
  -H "Content-Type: application/json" \\
  -d \'{"branch": "all", "period": "next_month"}\' | jq .
```

### 5. Coffee & Milkshake Growth Strategy
Get data-driven strategies to increase coffee and milkshake sales.
```bash
curl -s -X POST "$CONUT_API_URL/growth" \\
  -H "Content-Type: application/json" \\
  -d \'{"category": "all"}\' | jq .
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
'''


def generate_skill_file(output_dir: Path) -> Path:
    """Write the OpenClaw SKILL.md file to the specified directory."""
    skill_dir = output_dir / "conut-ops"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(SKILL_MD, encoding="utf-8")
    log.info(f"OpenClaw skill written to {skill_path}")
    return skill_path


class OpenClawWebhook:
    """Client for pushing notifications to OpenClaw webhooks."""

    def __init__(
        self,
        gateway_url: str = OPENCLAW_GATEWAY_URL,
        token: str = OPENCLAW_HOOK_TOKEN,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def wake(self, text: str, mode: str = "now") -> int:
        """Send a simple wake event to OpenClaw (synchronous)."""
        resp = httpx.post(
            f"{self.gateway_url}/hooks/wake",
            json={"text": text, "mode": mode},
            headers=self._headers(),
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.status_code

    def agent(
        self,
        message: str,
        name: str = "Conut-Ops",
        channel: Optional[str] = "last",
        deliver: bool = True,
        timeout_seconds: int = 120,
    ) -> int:
        """Trigger an agent turn with a message and deliver response to channel."""
        resp = httpx.post(
            f"{self.gateway_url}/hooks/agent",
            json={
                "message": message,
                "name": name,
                "wakeMode": "now",
                "deliver": deliver,
                "channel": channel,
                "timeoutSeconds": timeout_seconds,
            },
            headers=self._headers(),
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.status_code
