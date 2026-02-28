"""Feature engineering for demand forecasting."""

import pandas as pd


def build_branch_timeseries(monthly_sales: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build per-branch monthly time series for demand forecasting.

    Returns dict mapping branch name -> DataFrame with columns [date, total].
    """
    result = {}
    for branch, group in monthly_sales.groupby("branch"):
        ts = group[["year", "month_num", "total"]].copy()
        ts["date"] = pd.to_datetime(
            ts["year"].astype(str) + "-" + ts["month_num"].astype(str) + "-01"
        )
        ts = ts.sort_values("date").reset_index(drop=True)
        result[branch] = ts[["date", "total"]]
    return result
