from __future__ import annotations
from pathlib import Path
import re
import pandas as pd

from eda.src.io_utils import read_report_csv, to_float, to_float_money

_PERSON_RE = re.compile(r"^Person_\d+")
_BRANCHES = {"Conut - Tyre", "Conut", "Conut Jnah", "Main Street Coffee"}

def parse_customer_orders(path: Path) -> pd.DataFrame:
    """
    Parses rep_s_00150.csv into a clean table:
      branch, customer, phone, first_order_dt, last_order_dt, total_spend, orders

    Notes:
    - Report exports can contain malformed lines (handled in read_report_csv via on_bad_lines='skip')
    - Some rows appear before a branch header -> we skip those safely.
    - Dates can be in mixed formats -> dayfirst=True helps with dd/mm style.
    """
    raw = read_report_csv(path)

    branch: str | None = None
    rows: list[dict] = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None

        # ---- Branch marker ----
        if isinstance(c0, str) and c0.strip() in _BRANCHES:
            branch = c0.strip()
            continue

        # ---- Skip obvious report noise ----
        if isinstance(c0, str):
            t = c0.strip()
            if t == "" or "From Date" in t or "Page" in t or t.startswith("Total"):
                continue
            if t in {"Customer Name", "Address", "Phone Number", "First Order", "Last Order"}:
                continue

        # ---- Data row starts with Person_XXXX ----
        if isinstance(c0, str) and _PERSON_RE.match(c0.strip()):
            # If branch hasn't been detected yet, ignore this row (prevents branch=None groups)
            if branch is None:
                continue

            customer = c0.strip()

            phone = r.iloc[2] if len(r) > 2 else None
            first_order = r.iloc[3] if len(r) > 3 else None
            last_order = r.iloc[5] if len(r) > 5 else None
            total = to_float_money(r.iloc[7] if len(r) > 7 else None)
            n_orders = to_float(r.iloc[8] if len(r) > 8 else None)

            rows.append({
                "branch": branch,
                "customer": customer,
                "phone": str(phone).strip() if isinstance(phone, str) else None,
                # Robust datetime parse for report exports
                "first_order_dt": pd.to_datetime(first_order, errors="coerce", dayfirst=True),
                "last_order_dt": pd.to_datetime(last_order, errors="coerce", dayfirst=True),
                "total_spend": float(total) if pd.notna(total) else 0.0,
                "orders": float(n_orders) if pd.notna(n_orders) else 0.0
            })

    df = pd.DataFrame(rows)

    # Ensure correct dtypes
    if not df.empty:
        df["total_spend"] = pd.to_numeric(df["total_spend"], errors="coerce").fillna(0.0)
        df["orders"] = pd.to_numeric(df["orders"], errors="coerce").fillna(0.0)

    return df