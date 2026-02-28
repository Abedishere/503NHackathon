"""Tests for staffing estimator model."""

import pytest
from src.services.operations_agent import OperationsAgent


class TestStaffingEstimator:
    @pytest.fixture(scope="class")
    def agent(self):
        return OperationsAgent()

    def test_returns_valid_structure(self, agent):
        result = agent.staffing(branch="all")
        assert result["objective"] == "staffing_estimation"
        assert "scores" in result
        assert "actions" in result

    def test_shifts_present(self, agent):
        result = agent.staffing(branch="all")
        for score in result["scores"]:
            assert "branch" in score
            assert "shifts" in score
