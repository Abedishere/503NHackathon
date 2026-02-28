"""End-to-end smoke test: pipeline + models + API endpoint check."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.operations_agent import OperationsAgent
from src.utils.logging import get_logger

log = get_logger("smoke_test")


def main():
    log.info("=== Smoke Test ===")
    agent = OperationsAgent()

    tests = [
        ("combo", lambda: agent.combo(top_n=5)),
        ("demand", lambda: agent.demand(branch="all", horizon_months=2)),
        ("expansion", lambda: agent.expansion(risk_tolerance="moderate")),
        ("staffing", lambda: agent.staffing(branch="all")),
        ("growth", lambda: agent.growth(category="all")),
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        try:
            result = func()
            assert "objective" in result, "Missing 'objective' key"
            assert "scores" in result, "Missing 'scores' key"
            assert "rationale" in result, "Missing 'rationale' key"
            assert "confidence" in result, "Missing 'confidence' key"
            assert "actions" in result, "Missing 'actions' key"
            log.info(f"  PASS: {name} (confidence={result['confidence']}, actions={len(result['actions'])})")
            passed += 1
        except Exception as e:
            log.error(f"  FAIL: {name} — {e}")
            failed += 1

    log.info(f"=== Results: {passed} passed, {failed} failed ===")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
