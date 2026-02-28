"""Run all models and save results to artifacts."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.operations_agent import OperationsAgent
from src.config import ARTIFACTS_DIR
from src.utils.logging import get_logger

log = get_logger("train")


def main():
    log.info("=== Running all models ===")
    agent = OperationsAgent()

    objectives = {
        "combo": lambda: agent.combo(min_support=0.01, min_lift=1.0, top_n=15),
        "demand": lambda: agent.demand(branch="all", horizon_months=3),
        "expansion": lambda: agent.expansion(risk_tolerance="moderate"),
        "staffing": lambda: agent.staffing(branch="all", period="next_month"),
        "growth": lambda: agent.growth(category="all"),
    }

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    for name, func in objectives.items():
        log.info(f"Running {name}...")
        result = func()
        out_path = ARTIFACTS_DIR / f"{name}_result.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        log.info(f"  Saved {out_path}")
        log.info(f"  Confidence: {result.get('confidence', 'N/A')}")
        log.info(f"  Actions: {result.get('actions', [])}")

    log.info("=== All models complete ===")


if __name__ == "__main__":
    main()
