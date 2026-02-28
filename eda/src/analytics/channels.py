from __future__ import annotations
import pandas as pd

def channel_shares(menu_mix: pd.DataFrame) -> pd.DataFrame:
    """
    Input: menu_mix with columns: branch, menu, sales, (optional customers, avg_customer)
    Output: DataFrame with a real 'branch' column + 'sales_share'
    Compatible with pandas 3 groupby/apply behavior.
    """
    df = menu_mix.copy()

    # Ensure expected columns exist
    if "branch" not in df.columns:
        # If branch somehow ended up as index, bring it back
        df = df.reset_index()

    df["sales"] = pd.to_numeric(df.get("sales", 0.0), errors="coerce").fillna(0.0)

    # Compute share per branch without groupby.apply (more stable)
    totals = df.groupby("branch")["sales"].transform("sum")
    df["sales_share"] = df["sales"] / totals.replace({0: pd.NA})
    df["sales_share"] = df["sales_share"].fillna(0.0)

    return df