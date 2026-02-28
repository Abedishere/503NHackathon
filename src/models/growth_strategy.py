"""Coffee and milkshake growth strategy analysis."""

import pandas as pd
from src.features.growth_features import (
    build_category_performance,
    find_combo_affinities,
    COFFEE_KEYWORDS,
    MILKSHAKE_KEYWORDS,
)
from src.utils.logging import get_logger

log = get_logger(__name__)


def run_growth_strategy(
    item_sales: pd.DataFrame,
    sales_detail: pd.DataFrame,
    customer_orders: pd.DataFrame,
    category: str = "all",
) -> dict:
    """Develop data-driven growth strategies for coffee and milkshake categories.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    """
    perf = build_category_performance(item_sales)

    if perf.empty:
        return {
            "scores": [],
            "rationale": "No item sales data available.",
            "confidence": 0.0,
            "actions": [],
            "data": {},
        }

    # Aggregate across branches
    cat_summary = perf.groupby("category").agg(
        total_qty=("total_qty", "sum"),
        total_revenue=("total_revenue", "sum"),
        num_items=("num_items", "sum"),
    ).reset_index()

    grand_total = cat_summary["total_revenue"].sum()
    cat_summary["revenue_share"] = cat_summary["total_revenue"] / grand_total if grand_total > 0 else 0

    scores = []
    for _, row in cat_summary.iterrows():
        if category != "all" and row["category"] != category:
            continue
        if row["category"] == "other" and category == "all":
            continue

        share = float(row["revenue_share"])
        # Assess growth potential based on current share and item diversity
        if share < 0.10:
            potential = "high"
        elif share < 0.25:
            potential = "moderate"
        else:
            potential = "mature"

        scores.append({
            "category": row["category"],
            "current_share": round(share, 4),
            "total_revenue": round(float(row["total_revenue"]), 2),
            "total_qty": int(row["total_qty"]),
            "num_items": int(row["num_items"]),
            "growth_potential": potential,
        })

    # Find cross-sell opportunities
    co_items = find_combo_affinities(sales_detail)

    # Customer repeat analysis for coffee/milkshake buyers
    repeat_cust = customer_orders[customer_orders["num_orders"] > 1]
    total_repeat = len(repeat_cust)
    total_cust = len(customer_orders)
    repeat_pct = total_repeat / total_cust if total_cust > 0 else 0

    actions = []
    for s in scores:
        if s["category"] == "coffee":
            if s["growth_potential"] in ("high", "moderate"):
                actions.append(
                    f"Coffee ({s['current_share']:.0%} revenue share) has {s['growth_potential']} growth potential. "
                    "Launch a loyalty program targeting repeat customers."
                )
                actions.append("Introduce seasonal/limited-edition coffee drinks to drive trial.")
            else:
                actions.append("Coffee is a mature category. Focus on margin optimization and premium upsells.")

        elif s["category"] == "milkshake":
            if s["growth_potential"] in ("high", "moderate"):
                actions.append(
                    f"Milkshakes ({s['current_share']:.0%} revenue share) have {s['growth_potential']} growth potential. "
                    "Bundle with top-selling pastry items."
                )
                actions.append("Test afternoon milkshake promotion (2-5 PM discount) to capture off-peak demand.")
            else:
                actions.append("Milkshakes are performing well. Expand flavor variety to maintain momentum.")

    if not co_items.empty:
        top_co = co_items.head(3)["description"].tolist()
        actions.append(f"Cross-sell opportunity: customers who buy coffee/milkshakes also buy {', '.join(top_co)}.")

    return {
        "scores": scores,
        "rationale": "Category performance analysis cross-referenced with combo affinities and customer repeat rates.",
        "confidence": 0.70,
        "actions": actions,
        "data": {
            "items_analyzed": len(item_sales),
            "customer_repeat_rate": round(repeat_pct, 3),
            "top_cross_sell_items": co_items.head(5)["description"].tolist() if not co_items.empty else [],
        },
    }
