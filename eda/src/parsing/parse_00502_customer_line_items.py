from __future__ import annotations
from pathlib import Path
import re
import pandas as pd

from eda.src.io_utils import read_report_csv, to_float, to_float_money

_PERSON_RE = re.compile(r"^Person_\d+")

def _is_person_id(s: str) -> bool:
    return isinstance(s, str) and bool(_PERSON_RE.match(s.strip()))

def parse_customer_line_items(path: Path) -> pd.DataFrame:
    """
    Parses REP_S_00502.csv into a clean table:
    branch, customer, qty, item, price
    """
    raw = read_report_csv(path)

    branch = None
    customer = None
    rows = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None
        c1 = r.iloc[1] if len(r) > 1 else None
        c2 = r.iloc[2] if len(r) > 2 else None
        c3 = r.iloc[3] if len(r) > 3 else None

        # Branch marker: "Branch :Conut - Tyre"
        if isinstance(c0, str) and "Branch :" in c0:
            branch = c0.split("Branch :", 1)[-1].strip()
            continue

        # Customer marker: "Person_XXXX"
        if _is_person_id(c0):
            customer = c0.strip()
            continue

        # Skip totals/headers/pages
        if isinstance(c0, str) and (c0.startswith("Total") or "From Date:" in c0 or "Page" in c0):
            continue

        qty = to_float(c1)
        desc = c2
        price = to_float_money(c3)

        if branch and customer and pd.notna(qty) and isinstance(desc, str) and desc.strip():
            rows.append({
                "branch": branch,
                "customer": customer,
                "qty": float(qty),
                "item": re.sub(r"\s+", " ", desc.strip()),
                "price": float(price) if pd.notna(price) else 0.0,
            })

    return pd.DataFrame(rows)