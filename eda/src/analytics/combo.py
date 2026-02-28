from __future__ import annotations
from itertools import combinations
from collections import Counter
import pandas as pd
import numpy as np

def net_customer_items(line_items: pd.DataFrame, exclude_charge_keywords=("DELIVERY CHARGE","SERVICE","CHARGE")) -> pd.DataFrame:
    """
    Input: branch, customer, qty, item, price
    Output: branch, customer, item, net_qty, net_sales (positive only), and charge filtered out
    """
    net = (line_items
           .groupby(["branch","customer","item"], as_index=False)
           .agg(net_qty=("qty","sum"), net_sales=("price","sum")))

    net = net[net["net_qty"] > 0].copy()
    up = net["item"].str.upper()
    mask_charge = False
    for k in exclude_charge_keywords:
        mask_charge = mask_charge | up.str.contains(k)
    net = net[~mask_charge].copy()
    return net

def basket_sizes(net_pos: pd.DataFrame) -> pd.DataFrame:
    return (net_pos.groupby(["branch","customer"])["item"]
            .nunique()
            .reset_index(name="unique_items_in_basket"))

def top_items(net_pos: pd.DataFrame, branch: str | None = None, k: int = 15, by: str = "net_sales") -> pd.DataFrame:
    df = net_pos.copy()
    if branch is not None:
        df = df[df["branch"] == branch]
    agg = (df.groupby("item", as_index=False)
           .agg(net_qty=("net_qty","sum"), net_sales=("net_sales","sum")))
    return agg.sort_values(by, ascending=False).head(k)

def mine_pairs(net_pos: pd.DataFrame, branch: str | None = None, min_support_customers: int = 6) -> pd.DataFrame:
    """
    Customer-period pair mining. Reports support + lift-like score.
    Safe when no pairs meet the minimum support.
    """
    df = net_pos.copy()
    if branch is not None:
        df = df[df["branch"] == branch]

    baskets = (df.groupby(["branch","customer"])["item"]
               .apply(lambda x: sorted(set(x)))
               .reset_index(name="items"))

    pair_counts = Counter()
    item_counts = Counter()
    n_baskets = len(baskets)

    for items in baskets["items"]:
        for it in items:
            item_counts[it] += 1
        for a, b in combinations(items, 2):
            pair_counts[(a, b)] += 1

    rows = []
    for (a, b), cnt in pair_counts.items():
        if cnt < min_support_customers:
            continue
        support = cnt / n_baskets if n_baskets else 0.0
        pa = item_counts[a] / n_baskets if n_baskets else 0.0
        pb = item_counts[b] / n_baskets if n_baskets else 0.0
        lift = support / (pa * pb) if pa > 0 and pb > 0 else np.nan
        rows.append({
            "item_a": a,
            "item_b": b,
            "pair_customers": cnt,
            "support": support,
            "lift": lift
        })

    # ✅ If no rows, return an empty dataframe with the expected columns
    if not rows:
        return pd.DataFrame(columns=["item_a", "item_b", "pair_customers", "support", "lift"])

    return pd.DataFrame(rows).sort_values(["lift", "pair_customers"], ascending=False)

def try_association_rules(net_pos: pd.DataFrame, branch: str | None = None, min_support: float = 0.03, min_lift: float = 1.3):
    """
    Optional FP-growth association rules using mlxtend.
    Returns (freq_itemsets_df, rules_df) or (None, None).
    """
    try:
        from mlxtend.frequent_patterns import fpgrowth, association_rules
    except Exception:
        return None, None

    df = net_pos.copy()
    if branch is not None:
        df = df[df["branch"] == branch]

    baskets = (df.groupby(["customer"])["item"]
               .apply(lambda x: sorted(set(x)))
               .reset_index(name="items"))

    all_items = sorted({it for items in baskets["items"] for it in items})
    mat = np.zeros((len(baskets), len(all_items)), dtype=int)
    idx = {it:i for i,it in enumerate(all_items)}

    for r_i, items in enumerate(baskets["items"]):
        for it in items:
            mat[r_i, idx[it]] = 1

    trans = pd.DataFrame(mat, columns=all_items).astype(bool)
    freq = fpgrowth(trans, min_support=min_support, use_colnames=True)
    rules = association_rules(freq, metric="lift", min_threshold=min_lift)
    rules = rules.sort_values(["lift","confidence","support"], ascending=False)
    return freq, rules