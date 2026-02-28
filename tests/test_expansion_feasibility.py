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
