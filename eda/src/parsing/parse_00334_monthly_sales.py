from __future__ import annotations
from pathlib import Path
import pandas as pd
from eda.src.io_utils import read_report_csv, to_float_money

_MONTH_ORDER = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August","September","October","November","December"],
    start=1
)}

def parse_monthly_sales(path: Path) -> pd.DataFrame:
    """
    Parses rep_s_00334_1_SMRY.csv into:
    branch, year, month, period, sales
    """
    raw = read_report_csv(path)
    branch = None
    rows = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None
        c2 = r.iloc[2] if len(r) > 2 else None
        c3 = r.iloc[3] if len(r) > 3 else None

        if isinstance(c0, str) and c0.startswith("Branch Name:"):
            branch = c0.split("Branch Name:", 1)[-1].strip()
            continue

        if isinstance(c0, str) and c0.strip() in _MONTH_ORDER and isinstance(c2, str) and c2.strip().isdigit():
            year = int(c2.strip())
            month = c0.strip()
            sales = to_float_money(c3)
            if branch and pd.notna(sales):
                rows.append({"branch": branch, "year": year, "month": month, "sales": float(sales)})

    df = pd.DataFrame(rows)
    df["month_num"] = df["month"].map(_MONTH_ORDER)
    df["period"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month_num"].astype(str) + "-01", errors="coerce")
    return df.sort_values(["branch","period"])