"""Feature engineering for coffee and milkshake growth strategy."""

import pandas as pd


COFFEE_KEYWORDS = [
    "COFFEE", "CAPPUCCINO", "LATTE", "MOCHA", "ESPRESSO", "AMERICANO",
    "MACCHIATO", "FLAT WHITE", "HOT CHOCOLATE",
]

MILKSHAKE_KEYWORDS = [
    "MILKSHAKE", "SHAKE", "FRAPPE",
]


def _categorize_item(desc: str) -> str:
    desc_upper = desc.upper()
    for kw in COFFEE_KEYWORDS:
        if kw in desc_upper:
            return "coffee"
    for kw in MILKSHAKE_KEYWORDS:
        if kw in desc_upper:
            return "milkshake"
    return "other"


def build_category_performance(item_sales: pd.DataFrame) -> pd.DataFrame:
    """Classify items as coffee/milkshake/other and aggregate performance."""
    df = item_sales.copy()
    df["category"] = df["description"].apply(_categorize_item)

    perf = df.groupby(["branch", "category"]).agg(
        total_qty=("qty", "sum"),
        total_revenue=("total_amount", "sum"),
        num_items=("description", "nunique"),
    ).reset_index()

    # Compute share within branch
    branch_totals = perf.groupby("branch")["total_revenue"].sum().reset_index()
    branch_totals.columns = ["branch", "branch_total_revenue"]
    perf = perf.merge(branch_totals, on="branch")
    perf["revenue_share"] = perf["total_revenue"] / perf["branch_total_revenue"].clip(lower=1)

    return perf


def find_combo_affinities(
    sales_detail: pd.DataFrame, category_col: str = "description"
) -> pd.DataFrame:
    """Find which non-coffee/milkshake items most often co-occur with coffee/milkshake."""
    df = sales_detail.copy()
    df["category"] = df["description"].apply(_categorize_item)

    # Customers who bought coffee or milkshake
    target_customers = df[df["category"].isin(["coffee", "milkshake"])]["customer"].unique()

    # What else did those customers buy?
    co_items = df[
        (df["customer"].isin(target_customers)) & (df["category"] == "other")
    ]
    co_counts = co_items.groupby("description")["customer"].nunique().reset_index()
    co_counts.columns = ["description", "co_purchase_customers"]
    co_counts = co_counts.sort_values("co_purchase_customers", ascending=False)

    return co_counts.head(20)
