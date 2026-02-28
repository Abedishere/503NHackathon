from __future__ import annotations
from pathlib import Path
import pandas as pd

from eda.src.config import load_settings
from eda.src.parsing.parse_00502_customer_line_items import parse_customer_line_items
from eda.src.parsing.parse_00150_customer_orders import parse_customer_orders
from eda.src.parsing.parse_00191_items_by_group import parse_items_by_group
from eda.src.parsing.parse_00334_monthly_sales import parse_monthly_sales
from eda.src.parsing.parse_00435_menu_mix import parse_menu_mix
from eda.src.parsing.parse_00461_attendance import parse_attendance

from eda.src.analytics.combo import (
    net_customer_items,
    basket_sizes,
    top_items,
    mine_pairs,
    try_association_rules,
)
from eda.src.analytics.customers import rfm_lite_segments
from eda.src.analytics.demand import volatility
from eda.src.analytics.channels import channel_shares
from eda.src.analytics.staffing import daily_hours

# --- Advanced insights ---
from eda.src.analytics.branch_kpis import build_branch_kpis
from eda.src.analytics.combo_value import score_pairs_with_value_uplift
from eda.src.analytics.growth import growth_metrics

from eda.src.viz.plots import (
    plot_hist_basket_sizes,
    plot_top_items_bar,
    plot_monthly_sales,
    plot_channel_share,
    plot_daily_hours,
)

def run(
    eda_root: Path,
    *,
    save_assoc_rules: bool = False,   # default OFF (huge files)
    assoc_min_support: float = 0.05,  # higher default to keep it smaller if enabled
    assoc_min_lift: float = 1.4,
    scored_pairs_top_n: int = 200,    # keep commit-friendly
) -> None:
    """
    eda_root must be: .../503NHackathon/eda
    Produces clean tables + figures + advanced insight tables for Streamlit.

    Missing data handling:
    - Parsers already coerce/skip malformed lines.
    - Advanced insights degrade gracefully if some inputs are missing/empty.
    """

    settings = load_settings(eda_root)

    raw = settings.paths.data_raw
    out_tables = settings.paths.outputs_tables
    out_figs = settings.paths.outputs_figures

    out_tables.mkdir(parents=True, exist_ok=True)
    out_figs.mkdir(parents=True, exist_ok=True)

    # ---------- Load + Parse ----------
    line_items = parse_customer_line_items(raw / "REP_S_00502.csv")
    cust_orders = parse_customer_orders(raw / "rep_s_00150.csv")
    items_group = parse_items_by_group(raw / "rep_s_00191_SMRY.csv")
    monthly = parse_monthly_sales(raw / "rep_s_00334_1_SMRY.csv")
    menu_mix = parse_menu_mix(raw / "rep_s_00435_SMRY.csv")
    attendance = parse_attendance(raw / "REP_S_00461.csv")

    # ---------- Combo Prep ----------
    net_pos = net_customer_items(
        line_items,
        exclude_charge_keywords=settings.exclude_charge_keywords,
    )
    bsz = basket_sizes(net_pos)

    # ---------- Customer Segmentation ----------
    cust_seg = rfm_lite_segments(cust_orders)

    # ---------- Demand + Channels + Staffing ----------
    vol = volatility(monthly)
    ch_share = channel_shares(menu_mix)
    staff_daily = daily_hours(attendance)

    # ---------- Save clean tables ----------
    line_items.to_csv(out_tables / "customer_line_items_parsed.csv", index=False)
    net_pos.to_csv(out_tables / "net_customer_item_branch.csv", index=False)
    bsz.to_csv(out_tables / "basket_sizes.csv", index=False)

    cust_orders.to_csv(out_tables / "customer_orders_parsed.csv", index=False)
    cust_seg.to_csv(out_tables / "customer_rfm_lite.csv", index=False)

    items_group.to_csv(out_tables / "items_by_group_clean.csv", index=False)
    monthly.to_csv(out_tables / "monthly_sales_clean.csv", index=False)
    vol.to_csv(out_tables / "monthly_sales_volatility.csv", index=False)

    menu_mix.to_csv(out_tables / "menu_mix_clean.csv", index=False)
    ch_share.to_csv(out_tables / "channel_shares.csv", index=False)

    attendance.to_csv(out_tables / "attendance_clean.csv", index=False)
    staff_daily.to_csv(out_tables / "attendance_daily_hours.csv", index=False)

    # ---------- Advanced Insights: Branch KPIs ----------
    try:
        kpis = build_branch_kpis(net_pos, monthly, menu_mix, cust_orders)
        kpis.to_csv(out_tables / "branch_kpis.csv", index=False)
    except Exception as e:
        print("⚠️ Skipping branch_kpis due to error:", e)

    # ---------- Plots ----------
    plot_hist_basket_sizes(bsz, out_figs)
    plot_monthly_sales(monthly, out_figs)

    # ---------- Advanced Insights: per branch ----------
    all_scored_pairs = []
    all_growth = []
    all_coffee_xsell = []
    all_milk_xsell = []

    branches = sorted(net_pos["branch"].dropna().unique().tolist()) if "branch" in net_pos.columns else []

    for branch in branches:
        t_sales = top_items(net_pos, branch=branch, k=15, by="net_sales")
        t_qty = top_items(net_pos, branch=branch, k=15, by="net_qty")

        plot_top_items_bar(t_sales, branch, out_figs, metric="net_sales")
        plot_top_items_bar(t_qty, branch, out_figs, metric="net_qty")
        plot_channel_share(ch_share, branch, out_figs)
        plot_daily_hours(staff_daily, branch, out_figs)

        safe_branch = branch.replace(" ", "_")

        # ---------- Pair Mining (basic) ----------
        pairs = mine_pairs(
            net_pos,
            branch=branch,
            min_support_customers=settings.min_pair_support_customers,
        )
        pairs.to_csv(out_tables / f"combo_pairs_{safe_branch}.csv", index=False)

        # ---------- Pair Mining (scored + capped) ----------
        try:
            scored = score_pairs_with_value_uplift(
                net_pos=net_pos,
                cust_orders=cust_orders,
                branch=branch,
                min_support_customers=max(3, settings.min_pair_support_customers // 2),
                top_n=scored_pairs_top_n,
            )
            scored.to_csv(out_tables / f"combo_pairs_scored_{safe_branch}.csv", index=False)
            all_scored_pairs.append(scored)
        except Exception as e:
            print(f"⚠️ Skipping scored pairs for {branch} due to error:", e)

        # ---------- Coffee/Milkshake Growth Metrics ----------
        try:
            metrics, coffee_xsell, milk_xsell = growth_metrics(
                net_pos=net_pos,
                cust_orders=cust_orders,
                branch=branch,
                coffee_keywords=settings.coffee_keywords,
                milkshake_keywords=settings.milkshake_keywords,
                top_cross_sell=20,
            )
            metrics.to_csv(out_tables / f"growth_metrics_{safe_branch}.csv", index=False)
            all_growth.append(metrics)

            if isinstance(coffee_xsell, pd.DataFrame) and not coffee_xsell.empty:
                coffee_xsell.to_csv(out_tables / f"coffee_cross_sell_{safe_branch}.csv", index=False)
                all_coffee_xsell.append(coffee_xsell.assign(branch=branch))

            if isinstance(milk_xsell, pd.DataFrame) and not milk_xsell.empty:
                milk_xsell.to_csv(out_tables / f"milkshake_cross_sell_{safe_branch}.csv", index=False)
                all_milk_xsell.append(milk_xsell.assign(branch=branch))

        except Exception as e:
            print(f"⚠️ Skipping growth metrics for {branch} due to error:", e)

        # ---------- Optional association rules (OFF by default) ----------
        if save_assoc_rules:
            try:
                freq, rules = try_association_rules(
                    net_pos,
                    branch=branch,
                    min_support=assoc_min_support,
                    min_lift=assoc_min_lift,
                )
                # cap outputs to avoid huge files
                if rules is not None and freq is not None:
                    rules = rules.sort_values(["lift", "confidence"], ascending=False).head(5000)
                    freq = freq.sort_values(["support"], ascending=False).head(5000)

                    rules.to_csv(out_tables / f"assoc_rules_{safe_branch}.csv", index=False)
                    freq.to_csv(out_tables / f"freq_itemsets_{safe_branch}.csv", index=False)
            except Exception as e:
                print(f"⚠️ Association rules failed for {branch}:", e)

    # ---------- Global aggregated insight tables ----------
    if all_scored_pairs:
        pd.concat(all_scored_pairs, ignore_index=True).to_csv(
            out_tables / "combo_pairs_scored_all_branches.csv", index=False
        )

    if all_growth:
        pd.concat(all_growth, ignore_index=True).to_csv(
            out_tables / "growth_metrics_all_branches.csv", index=False
        )

    if all_coffee_xsell:
        pd.concat(all_coffee_xsell, ignore_index=True).to_csv(
            out_tables / "coffee_cross_sell_all_branches.csv", index=False
        )

    if all_milk_xsell:
        pd.concat(all_milk_xsell, ignore_index=True).to_csv(
            out_tables / "milkshake_cross_sell_all_branches.csv", index=False
        )

    print("\n✅ EDA complete.")
    print("Tables:", out_tables)
    print("Figures:", out_figs)
    print("Streamlit can now read outputs/tables/*.csv")