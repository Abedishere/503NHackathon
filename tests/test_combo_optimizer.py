"""Tests for combo optimization model."""

import pytest
from src.data.ingest_reports import parse_sales_detail
from src.data.clean_reports import clean_sales_detail
from src.models.combo_optimizer import run_combo_optimization


class TestComboOptimizer:
    @pytest.fixture(scope="class")
    def sales_data(self):
        raw = parse_sales_detail()
        return clean_sales_detail(raw)

    def test_returns_valid_structure(self, sales_data):
        result = run_combo_optimization(sales_data, min_support=0.02, min_lift=0.5, top_n=5)
        assert "scores" in result
        assert "rationale" in result
        assert "confidence" in result
        assert "actions" in result
        assert "data" in result

    def test_scores_have_items(self, sales_data):
        result = run_combo_optimization(sales_data, min_support=0.02, min_lift=0.5, top_n=5)
        for score in result["scores"]:
            assert "items" in score
            assert len(score["items"]) >= 2
            assert "lift" in score
