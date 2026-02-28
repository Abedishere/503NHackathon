from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def save_fig(figures_dir: Path, name: str):
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / name
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    print("Saved figure:", path)

def plot_hist_basket_sizes(basket_sizes: pd.DataFrame, figures_dir: Path):
    plt.figure()
    basket_sizes["unique_items_in_basket"].hist(bins=30)
    plt.xlabel("Unique items per customer-period basket")
    plt.ylabel("Count")
    plt.title("Basket Size Distribution (All Branches)")
    save_fig(figures_dir, "combo_basket_size_distribution.png")
    plt.close()

def plot_top_items_bar(top_items: pd.DataFrame, branch: str, figures_dir: Path, metric="net_sales"):
    plt.figure()
    d = top_items.sort_values(metric, ascending=True).tail(12)
    plt.barh(d["item"], d[metric])
    plt.xlabel(metric)
    plt.title(f"Top Items ({metric}) — {branch}")
    safe_branch = branch.replace(" ", "_")
    save_fig(figures_dir, f"top_items_{metric}_{safe_branch}.png")
    plt.close()

def plot_monthly_sales(monthly: pd.DataFrame, figures_dir: Path):
    plt.figure()
    for b in monthly["branch"].unique():
        d = monthly[monthly["branch"] == b]
        plt.plot(d["period"], d["sales"], marker="o", label=b)
    plt.xlabel("Month")
    plt.ylabel("Sales")
    plt.title("Monthly Sales Trend by Branch")
    plt.legend()
    save_fig(figures_dir, "monthly_sales_trend_by_branch.png")
    plt.close()

def plot_channel_share(channel_share: pd.DataFrame, branch: str, figures_dir: Path):
    if "branch" not in channel_share.columns:
        channel_share = channel_share.reset_index()
    d = channel_share[channel_share["branch"] == branch]
    plt.figure()
    plt.bar(d["menu"], d["sales_share"])
    plt.ylim(0, 1)
    plt.xlabel("Menu Channel")
    plt.ylabel("Sales Share")
    plt.title(f"Channel Sales Share — {branch}")
    safe_branch = branch.replace(" ", "_")
    save_fig(figures_dir, f"channel_share_{safe_branch}.png")
    plt.close()

def plot_daily_hours(daily_hours: pd.DataFrame, branch: str, figures_dir: Path):
    d = daily_hours[daily_hours["branch"] == branch].sort_values("date_in_dt")
    plt.figure()
    plt.plot(d["date_in_dt"], d["total_hours"], marker="o")
    plt.xlabel("Date")
    plt.ylabel("Total Work Hours")
    plt.title(f"Total Work Hours per Day — {branch}")
    safe_branch = branch.replace(" ", "_")
    save_fig(figures_dir, f"attendance_total_hours_{safe_branch}.png")
    plt.close()