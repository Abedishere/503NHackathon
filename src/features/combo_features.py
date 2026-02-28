"""Feature engineering for combo optimization (basket construction)."""

import pandas as pd


def build_baskets(sales_detail: pd.DataFrame) -> list[list[str]]:
    """Build transaction baskets from cleaned (netted) sales detail.

    Each basket is the set of distinct items a customer purchased.
    Free items (price=0) that are modifiers/toppings are excluded to focus
    on revenue-generating product combos.
    """
    # Filter to items with actual price > 0 (revenue items)
    paid = sales_detail[sales_detail["net_price"] > 0].copy()

    baskets = []
    for (_branch, customer), group in paid.groupby(["branch", "customer"]):
        items = group["description"].unique().tolist()
        if len(items) >= 2:  # Need at least 2 items for association rules
            baskets.append(items)

    return baskets
