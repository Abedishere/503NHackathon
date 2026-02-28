"""Tests for demand forecaster model."""

import pytest
from src.data.ingest_reports import parse_monthly_sales
from src.data.clean_reports import clean_monthly_sales
from src.models.demand_forecaster import run_demand_forecast


class TestDemandForecaster:
    @pytest.fixture(scope="class")
    def monthly_data(self):
        raw = parse_monthly_sales()
        return clean_monthly_sales(raw)

    def test_returns_valid_structure(self, monthly_data):
        result = run_demand_forecast(monthly_data, branch="all", horizon_months=2)
        assert result["scores"]
        assert result["rationale"]

    def test_forecasts_all_branches(self, monthly_data):
        result = run_demand_forecast(monthly_data, branch="all", horizon_months=3)
        branches = {s["branch"] for s in result["scores"]}
        assert len(branches) >= 3

    def test_forecast_has_confidence_bands(self, monthly_data):
        result = run_demand_forecast(monthly_data, branch="all", horizon_months=2)
        for score in result["scores"]:
            for f in score["forecast"]:
                assert "predicted" in f
                assert "lower" in f
                assert "upper" in f
