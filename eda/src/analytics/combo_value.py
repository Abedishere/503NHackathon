from __future__ import annotations
import pandas as pd
import numpy as np
from itertools import combinations
from collections import Counter

def score_pairs_with_value_uplift(
    net_pos: pd.DataFrame,
    cust_orders: pd.DataFrame | None,
    branch: str,
    min_support_customers: int = 3,
    top_n: int = 200,
) -> pd.DataFrame:
    """
    Pair mining for a branch with a value-uplift proxy:
      uplift = avg_total_spend(combo_customers) - avg_total_spend(all_customers)
    Works even if cust_orders is missing: uplift will be NaN.
    """
    df = net_pos[net_pos["branch"] == branch].copy()
    if df.empty:
        return pd.DataFrame(columns=["branch","item_a","item_b","pair_customers","support","lift","uplift_spend"])

    baskets = (df.groupby("customer")["item"].apply(lambda x: sorted(set(x))).reset_index(name="items"))

    pair_counts = Counter()
    item_counts = Counter()
    n_baskets = len(baskets)

    for items in baskets["items"]:
        for it in items:
            item_counts[it] += 1
        for a, b in combinations(items, 2):
            pair_counts[(a, b)] += 1

    # baseline spend by customer (optional)
    spend_map = None
    baseline_mean = np.nan
    if isinstance(cust_orders, pd.DataFrame) and {"branch","customer","total_spend"}.issubset(cust_orders.columns):
        co = cust_orders[cust_orders["branch"] == branch].copy()
        co["total_spend"] = pd.to_numeric(co["total_spend"], errors="coerce")
        spend_map = dict(zip(co["customer"], co["total_spend"]))
        baseline_mean = np.nanmean(list(spend_map.values())) if spend_map else np.nan

    rows = []
    for (a, b), cnt in pair_counts.items():
        if cnt < min_support_customers:
            continue
        support = cnt / n_baskets if n_baskets else 0.0
        pa = item_counts[a] / n_baskets if n_baskets else 0.0
        pb = item_counts[b] / n_baskets if n_baskets else 0.0
        lift = support / (pa * pb) if pa > 0 and pb > 0 else np.nan

        uplift = np.nan
        if spend_map is not None:
            # customers that contain both a and b
            combo_customers = baskets[baskets["items"].apply(lambda xs: (a in xs) and (b in xs))]["customer"]
            spends = [spend_map.get(c, np.nan) for c in combo_customers]
            uplift = np.nanmean(spends) - baseline_mean

        rows.append({
            "branch": branch,
            "item_a": a,
            "item_b": b,
            "pair_customers": cnt,
            "support": support,
            "lift": lift,
            "uplift_spend": uplift
        })

    if not rows:
        return pd.DataFrame(columns=["branch","item_a","item_b","pair_customers","support","lift","uplift_spend"])

    out = pd.DataFrame(rows)
    out = out.sort_values(["lift","pair_customers"], ascending=False).head(top_n)
    return out