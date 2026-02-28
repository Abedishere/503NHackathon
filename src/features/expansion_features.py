"""Feature engineering for expansion feasibility analysis."""

import pandas as pd
import numpy as np


def build_branch_health_scores(
    monthly_sales: pd.DataFrame,
    tax_summary: pd.DataFrame,
    customer_orders: pd.DataFrame,
    avg_menu_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Score each branch on health metrics for expansion analysis."""

    branches = monthly_sales["branch"].unique()
    records = []

    for branch in branches:
        branch_monthly = monthly_sales[monthly_sales["branch"] == branch]

        # Revenue trend (slope of monthly sales)
        if len(branch_monthly) >= 2:
            totals = branch_monthly.sort_values("month_num")["total"].values
            x = np.arange(len(totals))
            slope = np.polyfit(x, totals, 1)[0] if len(totals) > 1 else 0
            trend = "increasing" if slope > 0 else "decreasing"
        else:
            slope = 0
            trend = "flat"

        total_revenue = branch_monthly["total"].sum()

        # Customer metrics
        branch_cust = customer_orders[customer_orders["branch"] == branch]
        total_customers = len(branch_cust)
        repeat_customers = len(branch_cust[branch_cust["num_orders"] > 1])
        repeat_rate = repeat_customers / total_customers if total_customers > 0 else 0

        # Avg order value
        avg_order = branch_cust["total"].mean() if len(branch_cust) > 0 else 0

        # Tax contribution
        branch_tax = tax_summary[tax_summary["branch"] == branch]
        tax_total = branch_tax["total_tax"].sum() if len(branch_tax) > 0 else 0

        records.append({
            "branch": branch,
            "total_revenue": total_revenue,
            "revenue_slope": slope,
            "revenue_trend": trend,
            "num_customers": total_customers,
            "repeat_rate": repeat_rate,
            "avg_order_value": avg_order,
            "tax_contribution": tax_total,
            "months_active": len(branch_monthly),
        })

    return pd.DataFrame(records)
