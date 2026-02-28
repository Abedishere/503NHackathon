from __future__ import annotations
import pandas as pd
import numpy as np

def _contains_any(item: str, keywords: tuple[str, ...]) -> bool:
    if not isinstance(item, str):
        return False
    u = item.upper()
    return any(k in u for k in keywords)

def growth_metrics(
    net_pos: pd.DataFrame,
    cust_orders: pd.DataFrame | None,
    branch: str,
    coffee_keywords: tuple[str, ...],
    milkshake_keywords: tuple[str, ...],
    top_cross_sell: int = 20,
):
    """
    Returns:
      metrics_df (coffee/milkshake penetration + uplift proxies)
      coffee_xsell_df
      milkshake_xsell_df
    """
    df = net_pos[net_pos["branch"] == branch].copy()
    if df.empty:
        empty_m = pd.DataFrame(columns=["branch","segment","penetration_customers","avg_spend_buyers","avg_spend_nonbuyers","uplift"])
        return empty_m, pd.DataFrame(), pd.DataFrame()

    # customer sets
    cust_items = df.groupby("customer")["item"].apply(list)

    coffee_buyers = set(cust_items[cust_items.apply(lambda xs: any(_contains_any(x, coffee_keywords) for x in xs))].index)
    milk_buyers = set(cust_items[cust_items.apply(lambda xs: any(_contains_any(x, milkshake_keywords) for x in xs))].index)
    all_customers = set(cust_items.index)

    def spend_stats(buyers: set[str]):
        if not (isinstance(cust_orders, pd.DataFrame) and {"branch","customer","total_spend"}.issubset(cust_orders.columns)):
            return np.nan, np.nan, np.nan
        co = cust_orders[cust_orders["branch"] == branch].copy()
        co["total_spend"] = pd.to_numeric(co["total_spend"], errors="coerce")
        buyers_spend = co[co["customer"].isin(buyers)]["total_spend"]
        non_spend = co[~co["customer"].isin(buyers)]["total_spend"]
        return buyers_spend.mean(), non_spend.mean(), (buyers_spend.mean() - non_spend.mean())

    c_b, c_n, c_u = spend_stats(coffee_buyers)
    m_b, m_n, m_u = spend_stats(milk_buyers)

    def penetration(buyers: set[str]):
        return (len(buyers) / len(all_customers)) if all_customers else 0.0

    metrics = pd.DataFrame([
        {
            "branch": branch,
            "segment": "coffee",
            "penetration_customers": penetration(coffee_buyers),
            "avg_spend_buyers": c_b,
            "avg_spend_nonbuyers": c_n,
            "uplift": c_u
        },
        {
            "branch": branch,
            "segment": "milkshake",
            "penetration_customers": penetration(milk_buyers),
            "avg_spend_buyers": m_b,
            "avg_spend_nonbuyers": m_n,
            "uplift": m_u
        },
    ])

    # cross-sell: items bought by buyers excluding the anchor itself
    def cross_sell(buyers: set[str], anchor_keywords: tuple[str, ...]):
        sub = df[df["customer"].isin(buyers)].copy()
        sub["is_anchor"] = sub["item"].apply(lambda x: _contains_any(x, anchor_keywords))
        sub = sub[~sub["is_anchor"]]
        out = sub.groupby("item").agg(
            customers=("customer","nunique"),
            qty=("net_qty","sum"),
            sales=("net_sales","sum"),
        ).reset_index()
        return out.sort_values(["customers","sales"], ascending=False).head(top_cross_sell)

    coffee_xsell = cross_sell(coffee_buyers, coffee_keywords)
    milk_xsell = cross_sell(milk_buyers, milkshake_keywords)

    return metrics, coffee_xsell, milk_xsell