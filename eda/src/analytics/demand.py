from __future__ import annotations
import pandas as pd

def volatility(monthly_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Input: branch, period, sales
    Output: mean/std/min/max/cv per branch
    """
    vol = (monthly_sales.groupby("branch")["sales"]
           .agg(mean="mean", std="std", min="min", max="max")
           .assign(cv=lambda x: x["std"] / x["mean"]))
    return vol.sort_values("cv", ascending=False)