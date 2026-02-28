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

    def test_no_duplicate_itemsets(self, sales_data):
        """Each unique sorted itemset must appear only once in the top-N results (audit 4.5 fix)."""
        result = run_combo_optimization(sales_data, min_support=0.01, min_lift=1.0, top_n=10)
        seen = set()
        for score in result["scores"]:
            key = frozenset(score["items"])
            assert key not in seen, f"Duplicate itemset in combo scores: {score['items']}"
            seen.add(key)

    def test_actions_not_duplicated(self, sales_data):
        """Top-3 actions must all be distinct (audit 4.5 observable consequence fix)."""
        result = run_combo_optimization(sales_data, min_support=0.01, min_lift=1.0, top_n=10)
        actions = result["actions"]
        assert len(actions) == len(set(actions)), f"Duplicate actions found: {actions}"
