from __future__ import annotations
from pathlib import Path
import re
import pandas as pd
from eda.src.io_utils import read_report_csv, to_float

_BRANCHES = {"Conut - Tyre","Conut","Conut Jnah","Main Street Coffee"}
_DATE_RE = re.compile(r"\d{2}-[A-Za-z]{3}-\d{2}")

def _parse_duration_h(s: str):
    # "HH.MM.SS"
    if not isinstance(s, str) or not s.strip():
        return float("nan")
    parts = s.split(".")
    if len(parts) != 3:
        return float("nan")
    h, m, sec = [int(x) for x in parts]
    return h + m/60 + sec/3600

def parse_attendance(path: Path) -> pd.DataFrame:
    """
    Parses REP_S_00461.csv into:
    emp_id, emp_name, branch, date_in_dt, time_in, date_out, time_out, work_hours
    """
    raw = read_report_csv(path)

    emp_id = None
    emp_name = None
    branch = None
    rows = []

    for _, r in raw.iterrows():
        c0 = r.iloc[0] if len(r) > 0 else None
        c1 = r.iloc[1] if len(r) > 1 else None
        c2 = r.iloc[2] if len(r) > 2 else None
        c3 = r.iloc[3] if len(r) > 3 else None
        c4 = r.iloc[4] if len(r) > 4 else None
        c5 = r.iloc[5] if len(r) > 5 else None

        if isinstance(c1, str) and "EMP ID" in c1 and isinstance(c2, str) and "NAME" in c2:
            emp_id = to_float(c1.split("EMP ID :", 1)[-1])
            emp_name = c2.split("NAME :", 1)[-1].strip()
            continue

        if isinstance(c1, str) and c1.strip() in _BRANCHES:
            branch = c1.strip()
            continue

        if isinstance(c0, str) and _DATE_RE.match(c0.strip()):
            date_in = c0.strip()
            time_in = c2.strip() if isinstance(c2, str) else None
            date_out = c3.strip() if isinstance(c3, str) else None
            time_out = c4.strip() if isinstance(c4, str) else None
            duration = c5.strip() if isinstance(c5, str) else None

            rows.append({
                "emp_id": float(emp_id) if emp_id is not None else None,
                "emp_name": emp_name,
                "branch": branch,
                "date_in_dt": pd.to_datetime(date_in, format="%d-%b-%y", errors="coerce"),
                "time_in": time_in,
                "date_out": date_out,
                "time_out": time_out,
                "work_hours": _parse_duration_h(duration)
            })

    return pd.DataFrame(rows)