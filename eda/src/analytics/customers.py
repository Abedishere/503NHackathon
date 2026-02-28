from __future__ import annotations
import pandas as pd
import numpy as np


def _safe_qcut_ranked(series: pd.Series, q: int, labels, reverse: bool = False) -> pd.Series:
    """
    Robust qcut that:
    - drops NaNs
    - uses rank to break ties
    - handles non-unique bin edges with duplicates='drop'
    - falls back to 1-bin when not enough unique values
    """
    s = series.copy()
    out = pd.Series([None] * len(s), index=s.index, dtype="object")

    valid = s.dropna()
    if valid.empty:
        return out

    ranked = valid.rank(method="first")
    if reverse:
        # higher rank is worse -> reverse labels mapping later
        ranked = -ranked

    try:
        cut = pd.qcut(ranked, q=q, labels=labels, duplicates="drop")
        out.loc[valid.index] = cut.astype(str)
        return out
    except Exception:
        # fallback: everything in one bucket
        out.loc[valid.index] = str(labels[-1]) if hasattr(labels, "__len__") else "1"
        return out


def rfm_lite_segments(customer_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Input columns expected:
      branch, customer, last_order_dt, total_spend, orders
    Output adds:
      recency_days, frequency, monetary, R_q, F_q, M_q, RFM

    This version is robust to:
    - NaT last_order_dt
    - branches with few customers
    - tied/duplicate values
    """
    df = customer_orders.copy()

    # Ensure datetimes exist
    if "last_order_dt" not in df.columns:
        df["last_order_dt"] = pd.to_datetime(None)

    df["last_order_dt"] = pd.to_datetime(df["last_order_dt"], errors="coerce")

    # Compute a global reference date from valid timestamps only
    ref_date = df["last_order_dt"].dropna().max()
    if pd.isna(ref_date):
        # If everything is NaT, we cannot compute recency at all.
        # Return df with empty segment fields.
        df["recency_days"] = np.nan
        df["frequency"] = df.get("orders", np.nan)
        df["monetary"] = df.get("total_spend", np.nan)
        df["R_q"] = None
        df["F_q"] = None
        df["M_q"] = None
        df["RFM"] = None
        return df

    df["recency_days"] = (ref_date - df["last_order_dt"]).dt.days
    df["frequency"] = pd.to_numeric(df.get("orders", np.nan), errors="coerce")
    df["monetary"] = pd.to_numeric(df.get("total_spend", np.nan), errors="coerce")

    def seg(g: pd.DataFrame) -> pd.DataFrame:
        g = g.copy()

        # if an entire branch has no valid recency, don't crash
        if g["recency_days"].dropna().empty:
            g["R_q"] = None
        else:
            # Lower recency_days is better -> labels 4(best)..1(worst)
            g["R_q"] = _safe_qcut_ranked(g["recency_days"], q=4, labels=[4, 3, 2, 1], reverse=False)

        g["F_q"] = _safe_qcut_ranked(g["frequency"], q=4, labels=[1, 2, 3, 4], reverse=False)
        g["M_q"] = _safe_qcut_ranked(g["monetary"], q=4, labels=[1, 2, 3, 4], reverse=False)

        # Build RFM string safely
        g["RFM"] = (
            g["R_q"].fillna("0").astype(str)
            + g["F_q"].fillna("0").astype(str)
            + g["M_q"].fillna("0").astype(str)
        )
        return g

    return df.groupby("branch", group_keys=False).apply(seg)