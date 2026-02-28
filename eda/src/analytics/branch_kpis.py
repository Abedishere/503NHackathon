from __future__ import annotations
import pandas as pd
import numpy as np

def build_branch_kpis(
    net_pos: pd.DataFrame | None,
    monthly: pd.DataFrame | None,
    menu_mix: pd.DataFrame | None,
    cust_orders: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    Returns a branch KPI table even if some inputs are missing.
    Columns include:
      total_item_sales, unique_customers_items, unique_items_sold,
      monthly_mean, monthly_cv, growth_mom_last,
      delivery_share, table_share, takeaway_share,
      customer_total_spend, customer_avg_order_value
    """
    branches = set()

    for df, col in [(net_pos, "branch"), (monthly, "branch"), (menu_mix, "branch"), (cust_orders, "branch")]:
        if isinstance(df, pd.DataFrame) and col in df.columns:
            branches |= set(df[col].dropna().unique())

    if not branches:
        return pd.DataFrame(columns=["branch"])

    out = pd.DataFrame({"branch": sorted(branches)})

    # --- net_pos KPIs ---
    if isinstance(net_pos, pd.DataFrame) and {"branch", "customer", "item", "net_sales"}.issubset(net_pos.columns):
        g = net_pos.groupby("branch").agg(
            total_item_sales=("net_sales", "sum"),
            unique_customers_items=("customer", "nunique"),
            unique_items_sold=("item", "nunique"),
        ).reset_index()
        out = out.merge(g, on="branch", how="left")
    else:
        out["total_item_sales"] = np.nan
        out["unique_customers_items"] = np.nan
        out["unique_items_sold"] = np.nan

    # --- monthly KPIs ---
    if isinstance(monthly, pd.DataFrame) and {"branch", "sales", "period"}.issubset(monthly.columns):
        m = monthly.copy()
        m["sales"] = pd.to_numeric(m["sales"], errors="coerce")
        stats = m.groupby("branch")["sales"].agg(monthly_mean="mean", monthly_std="std").reset_index()
        stats["monthly_cv"] = stats["monthly_std"] / stats["monthly_mean"]
        out = out.merge(stats[["branch", "monthly_mean", "monthly_cv"]], on="branch", how="left")

        # last MoM growth (latest vs previous)
        m = m.sort_values(["branch", "period"])
        m["prev_sales"] = m.groupby("branch")["sales"].shift(1)
        m["mom_growth"] = (m["sales"] - m["prev_sales"]) / m["prev_sales"]
        last = m.dropna(subset=["sales"]).groupby("branch").tail(1)[["branch", "mom_growth"]]
        out = out.merge(last, on="branch", how="left").rename(columns={"mom_growth": "growth_mom_last"})
    else:
        out["monthly_mean"] = np.nan
        out["monthly_cv"] = np.nan
        out["growth_mom_last"] = np.nan

    # --- menu/channel shares ---
    if isinstance(menu_mix, pd.DataFrame) and {"branch", "menu", "sales"}.issubset(menu_mix.columns):
        mm = menu_mix.copy()
        mm["sales"] = pd.to_numeric(mm["sales"], errors="coerce").fillna(0.0)
        tot = mm.groupby("branch")["sales"].transform("sum").replace({0: np.nan})
        mm["share"] = (mm["sales"] / tot).fillna(0.0)
        pivot = mm.pivot_table(index="branch", columns="menu", values="share", aggfunc="sum").reset_index()
        pivot.columns = [str(c).lower().replace(" ", "_") if c != "branch" else "branch" for c in pivot.columns]
        for c in ["delivery", "table", "take_away"]:
            if c not in pivot.columns:
                pivot[c] = 0.0
        out = out.merge(pivot[["branch", "delivery", "table", "take_away"]], on="branch", how="left")
        out = out.rename(columns={"delivery": "delivery_share", "table": "table_share", "take_away": "takeaway_share"})
    else:
        out["delivery_share"] = np.nan
        out["table_share"] = np.nan
        out["takeaway_share"] = np.nan

    # --- customer spend KPIs ---
    if isinstance(cust_orders, pd.DataFrame) and {"branch", "total_spend", "orders"}.issubset(cust_orders.columns):
        co = cust_orders.copy()
        co["total_spend"] = pd.to_numeric(co["total_spend"], errors="coerce").fillna(0.0)
        co["orders"] = pd.to_numeric(co["orders"], errors="coerce").replace({0: np.nan})
        g = co.groupby("branch").agg(customer_total_spend=("total_spend", "sum")).reset_index()
        out = out.merge(g, on="branch", how="left")

        # average order value (proxy)
        co["aov"] = co["total_spend"] / co["orders"]
        aov = co.groupby("branch")["aov"].mean().reset_index(name="customer_avg_order_value")
        out = out.merge(aov, on="branch", how="left")
    else:
        out["customer_total_spend"] = np.nan
        out["customer_avg_order_value"] = np.nan

    return out