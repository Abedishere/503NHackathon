"""Feature engineering for staffing estimation."""

import pandas as pd
import numpy as np


def compute_staffing_metrics(
    attendance: pd.DataFrame,
    monthly_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Compute current staffing ratios per branch and shift period.

    For branches present in monthly_sales but absent from attendance
    (e.g. the main 'Conut' branch is absent from REP_S_00461.csv),
    a synthetic estimate is generated from the cross-branch median
    staffing-to-revenue ratio so those branches are still covered.
    """

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
    merged["_estimated"] = False  # Pre-set so concat doesn't produce mixed-type NaN

    # Identify branches present in monthly_sales but missing from attendance
    branches_with_attendance = set(avg_staff["branch"].unique())
    all_branches = set(branch_rev["branch"].unique())
    missing_branches = all_branches - branches_with_attendance

    if missing_branches and not merged.empty:
        # Compute median staffing metrics across known branches as fallback
        median_avg_staff = merged.groupby("shift")["avg_staff"].median()
        median_avg_hours = merged.groupby("shift")["avg_hours"].median()

        fallback_rows = []
        for branch in missing_branches:
            branch_revenue = branch_rev.loc[branch_rev["branch"] == branch, "avg_monthly_revenue"]
            rev = float(branch_revenue.iloc[0]) if len(branch_revenue) > 0 else 0.0
            for shift in ["morning", "evening", "night"]:
                est_staff = float(median_avg_staff.get(shift, 2.0))
                est_hours = float(median_avg_hours.get(shift, 6.0))
                rps = rev / max(est_staff, 1.0)
                fallback_rows.append({
                    "branch": branch,
                    "shift": shift,
                    "avg_staff": round(est_staff, 1),
                    "avg_hours": round(est_hours, 1),
                    "avg_monthly_revenue": rev,
                    "revenue_per_staff": rps,
                    "_estimated": True,
                })

        if fallback_rows:
            fallback_df = pd.DataFrame(fallback_rows)
            merged = pd.concat([merged, fallback_df], ignore_index=True)

    return merged
