"""OpenClaw liveness probe (env-gated).

Skips gracefully when OPENCLAW_GATEWAY_URL / OPENCLAW_HOOK_TOKEN are not set,
so it never blocks CI or local runs that have no OpenClaw instance available.

Usage:
    python scripts/check_openclaw_live.py

Required env vars (skip if absent):
    OPENCLAW_GATEWAY_URL   - e.g. http://127.0.0.1:18789
    OPENCLAW_HOOK_TOKEN    - bearer token for the gateway
"""

import json
import os
import sys
import time

import httpx

GATEWAY_URL = os.getenv("OPENCLAW_GATEWAY_URL", "").rstrip("/")
HOOK_TOKEN = os.getenv("OPENCLAW_HOOK_TOKEN", "")

LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "artifacts", "test_logs", "openclaw_checks.log"
)


def _log(msg: str) -> None:
    print(msg)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}\n")
    except OSError:
        pass


def _skip(reason: str) -> None:
    _log(f"SKIP -- {reason}")
    sys.exit(0)


def _fail(reason: str) -> None:
    _log(f"FAIL -- {reason}")
    sys.exit(1)


def _ok(msg: str) -> None:
    _log(f"OK   -- {msg}")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Env-gate: skip when credentials are absent
    # ------------------------------------------------------------------
    if not GATEWAY_URL:
        _skip("OPENCLAW_GATEWAY_URL not set -- skipping live probe")
    if not HOOK_TOKEN:
        _skip("OPENCLAW_HOOK_TOKEN not set -- skipping live probe")

    headers = {
        "Authorization": f"Bearer {HOOK_TOKEN}",
        "Content-Type": "application/json",
    }

    # ------------------------------------------------------------------
    # 2. Gateway reachability check
    # ------------------------------------------------------------------
    _log(f"Probing OpenClaw gateway: {GATEWAY_URL}")
    try:
        resp = httpx.get(f"{GATEWAY_URL}/health", headers=headers, timeout=10.0)
    except httpx.ConnectError as exc:
        _fail(f"Cannot reach OpenClaw gateway at {GATEWAY_URL}: {exc}")
    except httpx.TimeoutException:
        _fail(f"Timeout reaching OpenClaw gateway at {GATEWAY_URL}")

    if resp.status_code not in (200, 204):
        _fail(
            f"Gateway /health returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    _ok(f"Gateway /health -> HTTP {resp.status_code}")

    # ------------------------------------------------------------------
    # 3. Wake probe -- minimal agent interaction
    # ------------------------------------------------------------------
    _log("Sending wake probe to OpenClaw gateway ...")
    try:
        wake_resp = httpx.post(
            f"{GATEWAY_URL}/hooks/wake",
            json={"text": "Conut liveness check", "mode": "now"},
            headers=headers,
            timeout=30.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        _fail(f"Wake probe failed: {exc}")

    if wake_resp.status_code not in (200, 201, 202, 204):
        _fail(
            f"Wake probe returned HTTP {wake_resp.status_code}: {wake_resp.text[:200]}"
        )
    _ok(f"Wake probe -> HTTP {wake_resp.status_code}")

    # ------------------------------------------------------------------
    # 4. Agent query -- verify round-trip with a real business question
    # ------------------------------------------------------------------
    conut_api_url = os.getenv("CONUT_API_URL", "http://127.0.0.1:8000")
    _log("Sending agent query (combo endpoint probe) ...")
    try:
        agent_resp = httpx.post(
            f"{GATEWAY_URL}/hooks/agent",
            json={
                "message": (
                    f"Using the Conut Operations API at {conut_api_url}, "
                    "call POST /combo with min_support=0.01 and return the top combo."
                ),
                "name": "Conut-Ops",
                "wakeMode": "now",
                "deliver": False,
                "channel": "last",
                "timeoutSeconds": 60,
            },
            headers=headers,
            timeout=90.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        _fail(f"Agent query failed: {exc}")

    if agent_resp.status_code not in (200, 201, 202, 204):
        _fail(
            f"Agent query returned HTTP {agent_resp.status_code}: {agent_resp.text[:200]}"
        )

    try:
        body = agent_resp.json()
        _ok(f"Agent query -> HTTP {agent_resp.status_code}, response keys: {list(body.keys())}")
        _log(f"Agent response (truncated): {json.dumps(body)[:400]}")
    except Exception:
        _ok(f"Agent query -> HTTP {agent_resp.status_code} (non-JSON body)")

    _log("OpenClaw live probe PASSED -- all checks succeeded")


if __name__ == "__main__":
    main()
