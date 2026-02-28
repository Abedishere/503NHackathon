from __future__ import annotations
from pathlib import Path

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

from eda.src.viz.plots import (
    plot_hist_basket_sizes,
    plot_top_items_bar,
    plot_monthly_sales,
    plot_channel_share,
    plot_daily_hours,
)

def run(eda_root: Path) -> None:
    """
    eda_root must be: .../503NHackathon/eda
    """
    settings = load_settings(eda_root)

    raw = settings.paths.data_raw
    out_tables = settings.paths.outputs_tables
    out_figs = settings.paths.outputs_figures

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
    out_tables.mkdir(parents=True, exist_ok=True)

    line_items.to_csv(out_tables / "customer_line_items_parsed.csv", index=False)
    net_pos.to_csv(out_tables / "net_customer_item_branch.csv", index=False)
    bsz.to_csv(out_tables / "basket_sizes.csv", index=False)

    cust_orders.to_csv(out_tables / "customer_orders_parsed.csv", index=False)
    cust_seg.to_csv(out_tables / "customer_rfm_lite.csv", index=False)

    items_group.to_csv(out_tables / "items_by_group_clean.csv", index=False)
    monthly.to_csv(out_tables / "monthly_sales_clean.csv", index=False)
    vol.to_csv(out_tables / "monthly_sales_volatility.csv")

    menu_mix.to_csv(out_tables / "menu_mix_clean.csv", index=False)
    ch_share.to_csv(out_tables / "channel_shares.csv", index=False)

    attendance.to_csv(out_tables / "attendance_clean.csv", index=False)
    staff_daily.to_csv(out_tables / "attendance_daily_hours.csv", index=False)

    # ---------- Plots ----------
    plot_hist_basket_sizes(bsz, out_figs)
    plot_monthly_sales(monthly, out_figs)

    for branch in sorted(net_pos["branch"].unique()):
        t_sales = top_items(net_pos, branch=branch, k=15, by="net_sales")
        t_qty = top_items(net_pos, branch=branch, k=15, by="net_qty")

        plot_top_items_bar(t_sales, branch, out_figs, metric="net_sales")
        plot_top_items_bar(t_qty, branch, out_figs, metric="net_qty")
        plot_channel_share(ch_share, branch, out_figs)
        plot_daily_hours(staff_daily, branch, out_figs)

        # ---------- Pair Mining ----------
        pairs = mine_pairs(
            net_pos,
            branch=branch,
            min_support_customers=settings.min_pair_support_customers,
        )
        safe_branch = branch.replace(" ", "_")
        pairs.to_csv(out_tables / f"combo_pairs_{safe_branch}.csv", index=False)

        # ---------- Optional association rules ----------
        freq, rules = try_association_rules(net_pos, branch=branch, min_support=0.03, min_lift=1.3)
        if rules is not None and freq is not None:
            rules.to_csv(out_tables / f"assoc_rules_{safe_branch}.csv", index=False)
            freq.to_csv(out_tables / f"freq_itemsets_{safe_branch}.csv", index=False)

    print("\n✅ EDA complete.")
    print("Tables:", out_tables)
    print("Figures:", out_figs)