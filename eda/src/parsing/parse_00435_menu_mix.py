from __future__ import annotations
from pathlib import Path
import pandas as pd
from eda.src.io_utils import read_report_csv, to_float, to_float_money

_BRANCHES = {"Conut - Tyre","Conut","Conut Jnah","Main Street Coffee"}
_MENUS = {"DELIVERY","TABLE","TAKE AWAY"}

def parse_menu_mix(path: Path) -> pd.DataFrame:
    """
    Parses rep_s_00435_SMRY.csv into:
    branch, menu, customers, sales, avg_customer
    """
    raw = read_report_csv(path)
    branch = None
    rows = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None
        c1 = r.iloc[1] if len(r) > 1 else None
        c2 = r.iloc[2] if len(r) > 2 else None
        c3 = r.iloc[3] if len(r) > 3 else None

        if isinstance(c0, str) and c0.strip() in _BRANCHES:
            branch = c0.strip()
            continue

        if isinstance(c0, str) and c0.strip() in _MENUS:
            rows.append({
                "branch": branch,
                "menu": c0.strip(),
                "customers": float(to_float(c1)) if pd.notna(to_float(c1)) else 0.0,
                "sales": float(to_float_money(c2)) if pd.notna(to_float_money(c2)) else 0.0,
                "avg_customer": float(to_float_money(c3)) if pd.notna(to_float_money(c3)) else 0.0
            })

    return pd.DataFrame(rows)