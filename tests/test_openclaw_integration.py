"""Tests for OpenClaw integration components."""

import pytest
from pathlib import Path
from src.integrations.openclaw_tool import generate_skill_file, SKILL_MD


class TestOpenClawIntegration:
    def test_skill_md_contains_model_endpoints(self):
        """All 5 model endpoints must be documented in SKILL.md."""
        assert "/combo" in SKILL_MD
        assert "/demand" in SKILL_MD
        assert "/expansion" in SKILL_MD
        assert "/staffing" in SKILL_MD
        assert "/growth" in SKILL_MD
        assert "/health" in SKILL_MD

    def test_skill_md_contains_eda_endpoints(self):
        """All 6 EDA data endpoints must be documented in SKILL.md."""
        assert "/eda/branch-kpis" in SKILL_MD
        assert "/eda/combos" in SKILL_MD
        assert "/eda/growth" in SKILL_MD
        assert "/eda/channels" in SKILL_MD
        assert "/eda/staffing" in SKILL_MD
        assert "/eda/customers" in SKILL_MD

    def test_generate_skill_file(self, tmp_path):
        skill_path = generate_skill_file(tmp_path)
        assert skill_path.exists()
        content = skill_path.read_text()
        assert "conut-ops" in content
        assert "CONUT_API_URL" in content

    def test_skill_has_frontmatter(self):
        assert "name: conut-ops" in SKILL_MD
        assert "description:" in SKILL_MD

    def test_skill_documents_branch_filter(self):
        """Branch filter parameter must be documented for EDA endpoints."""
        assert "branch" in SKILL_MD
        assert "all" in SKILL_MD
