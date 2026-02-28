"""Tests for expansion feasibility model."""

import pytest
from src.services.operations_agent import OperationsAgent


class TestExpansionFeasibility:
    @pytest.fixture(scope="class")
    def agent(self):
        return OperationsAgent()

    def test_returns_valid_structure(self, agent):
        result = agent.expansion(risk_tolerance="moderate")
        assert result["objective"] == "expansion_feasibility"
        assert result["scores"]
        assert result["actions"]

    def test_scores_have_branch_info(self, agent):
        result = agent.expansion(risk_tolerance="moderate")
        for score in result["scores"]:
            assert "branch" in score
            assert "feasibility_score" in score
            assert "risk_level" in score

    def test_not_all_branches_decreasing(self, agent):
        """At least one branch must show increasing revenue trend (audit 4.7 fix).

        With correct parser values and partial-period exclusion, branches that
        grew Aug-Nov (e.g. Conut Jnah) should be labeled 'increasing'.
        """
        result = agent.expansion(risk_tolerance="moderate")
        trends = [s["revenue_trend"] for s in result["scores"]]
        assert "increasing" in trends, (
            f"All branches labeled 'decreasing'; partial-period fix may not be applied. Trends: {trends}"
        )

    def test_four_branches_analyzed(self, agent):
        """Expansion must analyze all 4 branches."""
        result = agent.expansion(risk_tolerance="moderate")
        assert result["data"]["branches_analyzed"] == 4, (
            f"Expected 4 branches, got {result['data']['branches_analyzed']}"
        )
