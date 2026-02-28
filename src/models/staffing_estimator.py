"""Shift staffing estimation using demand and attendance data."""

import numpy as np
import pandas as pd
from src.features.staffing_features import compute_staffing_metrics
from src.utils.logging import get_logger

log = get_logger(__name__)


def run_staffing_estimation(
    attendance: pd.DataFrame,
    monthly_sales: pd.DataFrame,
    branch: str = "all",
    period: str = "next_month",
) -> dict:
    """Estimate required staff per shift per branch.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    """
    metrics = compute_staffing_metrics(attendance, monthly_sales)

    if metrics.empty:
        return {
            "scores": [],
            "rationale": "No attendance data available for staffing analysis.",
            "confidence": 0.0,
            "actions": ["Ensure attendance tracking is operational."],
            "data": {},
        }

    if branch != "all":
        metrics = metrics[metrics["branch"] == branch]
        if metrics.empty:
            return {
                "scores": [],
                "rationale": f"No data for branch '{branch}'.",
                "confidence": 0.0,
                "actions": [],
                "data": {"available_branches": list(attendance["branch"].unique())},
            }

    # Compute recommended staffing based on revenue-per-staff benchmarks
    if "revenue_per_staff" in metrics.columns and metrics["revenue_per_staff"].notna().any():
        median_rps = metrics["revenue_per_staff"].median()
    else:
        median_rps = None

    scores = []
    branches_in_data = metrics["branch"].unique()

    for b in branches_in_data:
        b_metrics = metrics[metrics["branch"] == b]
        shifts = []
        for _, row in b_metrics.iterrows():
            current = round(float(row["avg_staff"]), 1)

            # Recommended: adjust based on revenue efficiency
            if median_rps and median_rps > 0 and "avg_monthly_revenue" in row and pd.notna(row["avg_monthly_revenue"]):
                ideal = row["avg_monthly_revenue"] / median_rps
                recommended = max(1, round(ideal, 1))
            else:
                recommended = current  # No adjustment possible

            gap = round(recommended - current, 1)
            shifts.append({
                "shift": row["shift"],
                "current_staff": current,
                "recommended_staff": recommended,
                "gap": gap,
                "avg_hours_per_shift": round(float(row["avg_hours"]), 1),
            })

        scores.append({"branch": b, "shifts": shifts})

    actions = []
    for s in scores:
        for shift in s["shifts"]:
            if shift["gap"] > 0.5:
                actions.append(
                    f"Hire {int(np.ceil(shift['gap']))} more {shift['shift']} staff at {s['branch']}."
                )
            elif shift["gap"] < -0.5:
                actions.append(
                    f"Reduce {shift['shift']} overstaffing at {s['branch']} by {int(np.ceil(abs(shift['gap'])))}."
                )

    if not actions:
        actions.append("Current staffing levels are well-aligned with demand.")

    return {
        "scores": scores,
        "rationale": "Staffing ratios computed from demand forecast vs. actual attendance hours.",
        "confidence": 0.70,
        "actions": actions,
        "data": {
            "attendance_records": len(attendance),
            "branches_analyzed": len(branches_in_data),
        },
    }
