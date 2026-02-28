"""Cleaning and validation pipeline for ingested report DataFrames."""

import pandas as pd
from src.utils.logging import get_logger

log = get_logger(__name__)

BRANCH_CANONICAL = {
    "Conut": "Conut",
    "Conut - Tyre": "Conut - Tyre",
    "Conut Jnah": "Conut Jnah",
    "Main Street Coffee": "Main Street Coffee",
}


def canonicalize_branch(df: pd.DataFrame, col: str = "branch") -> pd.DataFrame:
    if col in df.columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].map(BRANCH_CANONICAL).fillna(df[col])
    return df


def clean_sales_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Net negative-quantity returns per customer-order, drop zero-net items."""
    df = canonicalize_branch(df)
    df["description"] = df["description"].str.strip().str.strip(".")
    # Group by customer + description, net quantities
    grouped = df.groupby(["branch", "customer", "description"]).agg(
        net_qty=("qty", "sum"),
        net_price=("price", "sum"),
    ).reset_index()
    # Drop items with net qty <= 0
    cleaned = grouped[grouped["net_qty"] > 0].copy()
    log.info(f"Sales detail: {len(df)} raw -> {len(cleaned)} after netting returns")
    return cleaned


def clean_customer_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_branch(df)
    df["first_order"] = pd.to_datetime(df["first_order"], format="%Y-%m-%d %H:%M", errors="coerce")
    df["last_order"] = pd.to_datetime(df["last_order"], format="%Y-%m-%d %H:%M", errors="coerce")
    return df


def clean_attendance(df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_branch(df)
    # Filter out micro-punches (< 1 minute)
    df = df[df["hours_worked"] > 0.02].copy()
    # Parse dates
    df["date"] = pd.to_datetime(df["punch_in_date"], format="%d-%b-%y", errors="coerce")
    return df


def clean_monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_branch(df)
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    df["month_num"] = df["month"].map(month_map)
    df = df.sort_values(["branch", "year", "month_num"]).reset_index(drop=True)
    return df


def clean_item_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_branch(df)
    df["description"] = df["description"].str.strip().str.strip(".")
    return df


def clean_tax_summary(df: pd.DataFrame) -> pd.DataFrame:
    return canonicalize_branch(df)


def clean_division_summary(df: pd.DataFrame) -> pd.DataFrame:
    return canonicalize_branch(df)


def clean_avg_menu_sales(df: pd.DataFrame) -> pd.DataFrame:
    return canonicalize_branch(df)


def clean_all(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply per-dataset cleaning to all ingested data."""
    cleaners = {
        "division_summary": clean_division_summary,
        "tax_summary": clean_tax_summary,
        "attendance": clean_attendance,
        "sales_detail": clean_sales_detail,
        "customer_orders": clean_customer_orders,
        "item_sales": clean_item_sales,
        "monthly_sales": clean_monthly_sales,
        "avg_menu_sales": clean_avg_menu_sales,
    }
    cleaned = {}
    for key, df in datasets.items():
        if key in cleaners:
            cleaned[key] = cleaners[key](df)
        else:
            cleaned[key] = df
    return cleaned
