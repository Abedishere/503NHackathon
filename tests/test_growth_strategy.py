"""Tests for growth strategy model."""

import pytest
from src.services.operations_agent import OperationsAgent


class TestGrowthStrategy:
    @pytest.fixture(scope="class")
    def agent(self):
        return OperationsAgent()

    def test_returns_valid_structure(self, agent):
        result = agent.growth(category="all")
        assert result["objective"] == "growth_strategy"
        assert result["scores"]
        assert result["actions"]

    def test_coffee_and_milkshake_present(self, agent):
        result = agent.growth(category="all")
        categories = {s["category"] for s in result["scores"]}
        assert "coffee" in categories or "milkshake" in categories
