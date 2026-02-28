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

    def test_all_four_branches_covered(self, agent):
        """Staffing must cover all 4 branches including 'Conut' main (audit 4.3 fix).

        The 'Conut' main branch has no entries in the attendance CSV, so the
        staffing feature layer must generate an estimated fallback for it.
        """
        result = agent.staffing(branch="all")
        branches = {s["branch"] for s in result["scores"]}
        assert "Conut" in branches, (
            f"'Conut' main branch missing from staffing. Found: {branches}"
        )
        assert result["data"]["branches_analyzed"] == 4, (
            f"Expected 4 branches, got {result['data']['branches_analyzed']}"
        )

    def test_customer_orders_all_branches_attributed(self, agent):
        """customer_orders must have all 4 branches attributed (audit 4.6 fix)."""
        agent._ensure_loaded()
        co = agent._datasets["customer_orders"]
        null_branch = co["branch"].isna().sum()
        assert null_branch == 0, (
            f"{null_branch} customer_orders rows have branch=None; parser carry-over bug remains"
        )
