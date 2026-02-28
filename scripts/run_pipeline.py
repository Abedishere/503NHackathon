"""Run the full data pipeline: ingest -> clean -> validate -> save artifacts."""

import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.ingest_reports import ingest_all
from src.data.clean_reports import clean_all
from src.data.validate import validate_all
from src.config import ARTIFACTS_DIR
from src.utils.logging import get_logger

log = get_logger("pipeline")


def main():
    log.info("=== Starting data pipeline ===")

    log.info("Step 1: Ingesting reports...")
    raw = ingest_all()

    log.info("Step 2: Cleaning datasets...")
    cleaned = clean_all(raw)

    log.info("Step 3: Validating datasets...")
    warnings = validate_all(cleaned)

    log.info("Step 4: Saving cleaned data to artifacts...")
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    for key, df in cleaned.items():
        out_path = ARTIFACTS_DIR / f"{key}.csv"
        df.to_csv(out_path, index=False)
        log.info(f"  Saved {out_path} ({len(df)} rows)")

    # Save validation report
    val_path = ARTIFACTS_DIR / "validation_report.json"
    with open(val_path, "w") as f:
        json.dump(warnings, f, indent=2)
    log.info(f"  Saved {val_path}")

    log.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
