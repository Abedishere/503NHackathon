"""Feature engineering for staffing estimation."""

import pandas as pd
import numpy as np


def compute_staffing_metrics(
    attendance: pd.DataFrame,
    monthly_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Compute current staffing ratios per branch and shift period."""

    if attendance.empty:
        return pd.DataFrame()

    # Classify punch-in times into shifts
    def _classify_shift(time_str: str) -> str:
        if not time_str:
            return "unknown"
        try:
            hour = int(time_str.split(":")[0])
        except (ValueError, IndexError):
            return "unknown"
        if 6 <= hour < 14:
            return "morning"
        elif 14 <= hour < 22:
            return "evening"
        else:
            return "night"

    att = attendance.copy()
    att["shift"] = att["punch_in_time"].apply(_classify_shift)
    att = att[att["shift"] != "unknown"]

    # Average daily staff count per branch per shift
    if "date" in att.columns:
        daily = att.groupby(["branch", "shift", "date"]).agg(
            staff_count=("emp_id", "nunique"),
            total_hours=("hours_worked", "sum"),
        ).reset_index()

        avg_staff = daily.groupby(["branch", "shift"]).agg(
            avg_staff=("staff_count", "mean"),
            avg_hours=("total_hours", "mean"),
        ).reset_index()
    else:
        avg_staff = att.groupby(["branch", "shift"]).agg(
            avg_staff=("emp_id", "nunique"),
            avg_hours=("hours_worked", "mean"),
        ).reset_index()

    # Join with branch revenue for demand-based staffing ratio
    branch_rev = monthly_sales.groupby("branch")["total"].mean().reset_index()
    branch_rev.columns = ["branch", "avg_monthly_revenue"]

    merged = avg_staff.merge(branch_rev, on="branch", how="left")
    if not merged.empty and "avg_monthly_revenue" in merged.columns:
        merged["revenue_per_staff"] = merged["avg_monthly_revenue"] / merged["avg_staff"].clip(lower=1)

    return merged
