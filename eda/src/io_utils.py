from __future__ import annotations
from pathlib import Path
import pandas as pd


def read_report_csv(path: Path) -> pd.DataFrame:
    """
    Read report-style CSV (no stable headers, lots of blank columns, sometimes malformed lines).
    - Pandas 3 compatible (no DataFrame.applymap)
    - Skips malformed rows caused by report exports (extra commas, page breaks, etc.)
    """
    df = pd.read_csv(
        path,
        header=None,
        dtype=str,
        encoding="utf-8",
        engine="python",
        on_bad_lines="skip",   
    )

    # Drop fully empty columns
    df = df.dropna(axis=1, how="all")

    # Strip whitespace from all cells (vectorized per column)
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()

    # Convert pandas <NA> to None for consistent checks
    df = df.where(df.notna(), None)

    return df


def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)


def to_float(x):
    if x is None:
        return float("nan")
    s = str(x).strip().replace('"', "")
    if s == "" or s.lower() in {"nan", "none"}:
        return float("nan")
    try:
        return float(s)
    except Exception:
        return float("nan")


def to_float_money(x):
    """
    Convert strings like:
    - "1,251,486.48"
    - "-893,918.92"
    - "0.00"
    into float
    """
    if x is None:
        return float("nan")
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return float("nan")
    s = s.replace('"', "").replace(",", "")
    try:
        return float(s)
    except Exception:
        return float("nan")