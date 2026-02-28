"""Tests for data ingestion and cleaning pipeline."""

import pytest
from src.data.ingest_reports import (
    parse_division_summary,
    parse_tax_summary,
    parse_attendance,
    parse_sales_detail,
    parse_customer_orders,
    parse_item_sales,
    parse_monthly_sales,
    parse_avg_menu_sales,
)
from src.data.clean_reports import clean_all, clean_sales_detail


class TestIngestion:
    def test_parse_monthly_sales(self):
        df = parse_monthly_sales()
        assert not df.empty
        assert "branch" in df.columns
        assert "month" in df.columns
        assert "total" in df.columns
        # 4 branches, ~5 months each
        assert len(df) >= 15

    def test_parse_tax_summary(self):
        df = parse_tax_summary()
        assert not df.empty
        assert len(df) == 4  # 4 branches

    def test_parse_attendance(self):
        df = parse_attendance()
        assert not df.empty
        assert "emp_id" in df.columns
        assert "hours_worked" in df.columns

    def test_parse_sales_detail(self):
        df = parse_sales_detail()
        assert not df.empty
        assert "customer" in df.columns
        assert "qty" in df.columns
        assert "description" in df.columns

    def test_parse_customer_orders(self):
        df = parse_customer_orders()
        assert not df.empty
        assert "branch" in df.columns
        assert "num_orders" in df.columns

    def test_customer_orders_all_branches_present(self):
        """All 4 branches must be in customer_orders with no branch=None (audit 4.6 fix)."""
        df = parse_customer_orders()
        null_count = df["branch"].isna().sum()
        assert null_count == 0, (
            f"{null_count} rows have branch=None; 'Conut - Tyre' section header skip bug"
        )
        branches = set(df["branch"].unique())
        for expected in ("Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"):
            assert expected in branches, f"'{expected}' missing from customer_orders branches"

    def test_monthly_sales_totals_not_truncated(self):
        """Monthly sales totals must be full quoted-number values, not truncated (audit 4.2 root cause)."""
        df = parse_monthly_sales()
        # Conut Oct 2025: raw value is "1,137,352,241.41" -> must be ~1.137B not 1.0
        conut_oct = df[(df["branch"] == "Conut") & (df["month"] == "October")]
        assert not conut_oct.empty
        assert conut_oct["total"].iloc[0] > 1_000_000_000, (
            "Conut October total is not >1B; csv.reader fix for quoted numbers may be missing"
        )

    def test_parse_item_sales(self):
        df = parse_item_sales()
        assert not df.empty
        assert "division" in df.columns
        assert "qty" in df.columns

    def test_parse_avg_menu_sales(self):
        df = parse_avg_menu_sales()
        assert not df.empty
        assert "menu_type" in df.columns

    def test_parse_division_summary(self):
        df = parse_division_summary()
        assert not df.empty
        assert "branch" in df.columns


class TestCleaning:
    def test_clean_sales_detail_nets_returns(self):
        df = parse_sales_detail()
        cleaned = clean_sales_detail(df)
        # All net_qty should be > 0
        assert (cleaned["net_qty"] > 0).all()

    def test_clean_all(self):
        from src.data.ingest_reports import ingest_all
        raw = ingest_all()
        cleaned = clean_all(raw)
        assert len(cleaned) == 8
        for key, df in cleaned.items():
            assert not df.empty, f"{key} is empty after cleaning"
