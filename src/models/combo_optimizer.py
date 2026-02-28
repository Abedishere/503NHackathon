"""Combo optimization using association rule mining (Apriori / FP-Growth)."""

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from src.features.combo_features import build_baskets
from src.utils.logging import get_logger

log = get_logger(__name__)


def run_combo_optimization(
    sales_detail: pd.DataFrame,
    min_support: float = 0.01,
    min_lift: float = 1.0,
    top_n: int = 10,
) -> dict:
    """Run association rule mining on customer baskets.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    """
    baskets = build_baskets(sales_detail)
    total_transactions = len(baskets)

    if total_transactions < 5:
        return {
            "scores": [],
            "rationale": "Insufficient transaction data for association mining.",
            "confidence": 0.0,
            "actions": ["Collect more transaction data before running combo analysis."],
            "data": {"total_transactions": total_transactions, "unique_items": 0, "rules_found": 0},
        }

    te = TransactionEncoder()
    te_array = te.fit(baskets).transform(baskets)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    # Find frequent itemsets (limit to pairs/triples to avoid combinatorial explosion)
    frequent = apriori(df_encoded, min_support=min_support, use_colnames=True, max_len=3)

    if frequent.empty:
        return {
            "scores": [],
            "rationale": f"No frequent itemsets found at min_support={min_support}.",
            "confidence": 0.3,
            "actions": ["Lower min_support threshold or collect more data."],
            "data": {"total_transactions": total_transactions, "unique_items": len(te.columns_), "rules_found": 0},
        }

    # Generate association rules
    rules = association_rules(frequent, metric="lift", min_threshold=min_lift)

    if rules.empty:
        return {
            "scores": [],
            "rationale": f"No association rules found at min_lift={min_lift}.",
            "confidence": 0.3,
            "actions": ["Lower lift threshold."],
            "data": {"total_transactions": total_transactions, "unique_items": len(te.columns_), "rules_found": 0},
        }

    rules = rules.sort_values("lift", ascending=False)

    # Deduplicate by normalized sorted itemset key before top_n truncation.
    # Apriori produces A->B and B->A as separate rules; after merging
    # antecedents+consequents they look identical in the output.
    seen_itemsets: set[frozenset] = set()
    deduped_rows = []
    for _, row in rules.iterrows():
        itemset = frozenset(row["antecedents"] | row["consequents"])
        if itemset not in seen_itemsets:
            seen_itemsets.add(itemset)
            deduped_rows.append(row)
        if len(deduped_rows) >= top_n:
            break

    scores = []
    for row in deduped_rows:
        items = sorted(row["antecedents"] | row["consequents"])
        scores.append({
            "items": items,
            "support": round(float(row["support"]), 4),
            "confidence": round(float(row["confidence"]), 4),
            "lift": round(float(row["lift"]), 2),
        })

    # Generate actionable recommendations
    actions = []
    for s in scores[:3]:
        items_str = " + ".join(s["items"])
        actions.append(f"Bundle {items_str} as a combo (lift={s['lift']}x)")

    return {
        "scores": scores,
        "rationale": f"Top combos from {total_transactions} transactions using Apriori association mining.",
        "confidence": min(0.85, 0.5 + 0.1 * len(scores)),
        "actions": actions,
        "data": {
            "total_transactions": total_transactions,
            "unique_items": len(te.columns_),
            "rules_found": len(deduped_rows),
        },
    }
