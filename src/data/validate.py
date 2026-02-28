"""Dataset-level QA validation checks."""

import pandas as pd
from src.utils.logging import get_logger

log = get_logger(__name__)

EXPECTED_BRANCHES = {"Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"}


def validate_all(datasets: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """Run QA checks on all cleaned datasets. Returns dict of warnings per key."""
    warnings: dict[str, list[str]] = {}

    for key, df in datasets.items():
        w = []
        if df.empty:
            w.append(f"{key}: DataFrame is EMPTY")
        else:
            w.append(f"{key}: {len(df)} rows, {len(df.columns)} cols")
            null_pct = df.isnull().mean()
            high_null = null_pct[null_pct > 0.5]
            if not high_null.empty:
                for col, pct in high_null.items():
                    w.append(f"  HIGH NULL: {col} = {pct:.0%}")

        if "branch" in df.columns and not df.empty:
            found = set(df["branch"].dropna().unique())
            unknown = found - EXPECTED_BRANCHES
            if unknown:
                w.append(f"  UNKNOWN BRANCHES: {unknown}")

        warnings[key] = w
        for msg in w:
            log.info(msg)

    return warnings
