"""Feature engineering for demand forecasting."""

import pandas as pd
from src.features.time_series_utils import detect_partial_period_cutoff


def build_branch_timeseries(
    monthly_sales: pd.DataFrame,
    partial_period_threshold: float = 0.30,
) -> dict[str, pd.DataFrame]:
    """Build per-branch monthly time series for demand forecasting.

    Excludes anomalous trailing partial months (e.g. incomplete export months)
    from the returned series so the forecaster works on complete-period data.

    Returns dict mapping branch name -> DataFrame with columns [date, total].
    """
    result = {}
    for branch, group in monthly_sales.groupby("branch"):
        ts = group[["year", "month_num", "total"]].copy()
        ts["date"] = pd.to_datetime(
            ts["year"].astype(str) + "-" + ts["month_num"].astype(str) + "-01"
        )
        ts = ts.sort_values("date").reset_index(drop=True)

        values = ts["total"].values
        cutoff = detect_partial_period_cutoff(values, threshold=partial_period_threshold)
        ts = ts.iloc[:cutoff].reset_index(drop=True)

        result[branch] = ts[["date", "total"]]
    return result
