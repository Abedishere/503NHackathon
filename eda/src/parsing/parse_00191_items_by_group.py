from __future__ import annotations
from pathlib import Path
import pandas as pd
from eda.src.io_utils import read_report_csv, to_float, to_float_money

def parse_items_by_group(path: Path) -> pd.DataFrame:
    """
    Parses rep_s_00191_SMRY.csv into:
    branch, division, group, item, qty, sales
    """
    raw = read_report_csv(path)

    branch = None
    division = None
    group = None
    rows = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None
        c2 = r.iloc[2] if len(r) > 2 else None
        c3 = r.iloc[3] if len(r) > 3 else None

        if isinstance(c0, str) and c0.startswith("Branch:"):
            branch = c0.split("Branch:", 1)[-1].strip()
            continue
        if isinstance(c0, str) and c0.startswith("Division:"):
            division = c0.split("Division:", 1)[-1].strip()
            continue
        if isinstance(c0, str) and c0.startswith("Group:"):
            group = c0.split("Group:", 1)[-1].strip()
            continue

        if isinstance(c0, str) and (c0.startswith("Total") or "Page" in c0 or "From Date" in c0 or "Years:" in c0):
            continue
        if c0 in {"Description"}:
            continue

        qty = to_float(c2)
        sales = to_float_money(c3)

        if branch and division and group and isinstance(c0, str) and c0.strip() and pd.notna(qty):
            rows.append({
                "branch": branch,
                "division": division,
                "group": group,
                "item": c0.strip(),
                "qty": float(qty),
                "sales": float(sales) if pd.notna(sales) else 0.0
            })

    return pd.DataFrame(rows)