# Task

file:/C:/Users/Abed%20Al-Rahman/Desktop/AUB%20STUFF/503N%20Hackathon/AUDIT_REPORT.md i want you through this refrence file, to fix what is broken according to my personal testing

# Implementation Plan

---

**APPROVED**

The plan correctly maps to all 9 audit issues (4.8/weasyprint is acceptably out-of-scope since the PDF is pre-generated). Build order is correct — parsers first, then cleaning, then shared utilities, then model-layer fixes, then tests, then OpenClaw, then docs, then final validation. No circular dependencies, no missing files, and the technical decisions align with CLAUDE.md conventions.

One advisory note (not blocking): Step 3's partial-period heuristic is the linchpin fix for both audit 4.2 (negative forecasts) and 4.7 (all-decreasing trends). The implementer should ensure it **excludes** anomalous trailing months from trend/slope computation — not just clamp the output after the fact. The clamping in step 4 is a correct defensive layer, but partial-period exclusion is the primary fix.

---

1. **Files to create/modify**

- **Modify** `src/data/ingest_reports.py`
- **Modify** `src/data/clean_reports.py`
- **Modify** `src/data/validate.py`
- **Create** `src/features/time_series_utils.py`
- **Modify** `src/features/demand_features.py`
- **Modify** `src/features/expansion_features.py`
- **Modify** `src/features/staffing_features.py`
- **Modify** `src/models/demand_forecaster.py`
- **Modify** `src/models/combo_optimizer.py`
- **Modify** `src/models/expansion_feasibility.py`
- **Modify** `src/utils/logging.py`
- **Modify** `src/integrations/openclaw_tool.py`
- **Create** `scripts/check_openclaw_live.py`
- **Modify** `Makefile`
- **Modify** `tests/test_ingestion_cleaning.py`
- **Modify** `tests/test_combo_optimizer.py`
- **Modify** `tests/test_demand_forecaster.py`
- **Modify** `tests/test_expansion_feasibility.py`
- **Modify** `tests/test_staffing_estimator.py`
- **Modify** `tests/test_openclaw_integration.py`
- **Modify** `README.md`
- **Modify** `docs/openclaw-integration.md`
- **Create** `docs/evidence/README.md`
- **Modify** `docs/validation/test_run_report.md`

2. **Step-by-step build order**

1. Fix parser correctness in `ingest_reports.py` for quoted numerics, unstable headers/sections, branch carry-over, and customer row variants in `REP_S_00461.csv`, `REP_S_00502.csv`, and `rep_s_00150.csv`.
2. Tighten cleaning/validation in `clean_reports.py` and `validate.py` to enforce branch coverage, flag unattributed rows, and preserve usable records.
3. Implement one shared partial-period utility in `time_series_utils.py`, then wire it into `demand_features.py` and `expansion_features.py`.
4. Apply model-layer fixes: deduplicate combo itemsets (`combo_optimizer.py`), clamp demand outputs at boundary (`demand_forecaster.py`), and add expansion defensive trend guard (`expansion_feasibility.py`).
5. Fix log encoding artifact in `logging.py` and normalize action text to ASCII-safe output where needed.
6. Update and extend tests for parser branch coverage, non-negative demand bounds, combo deduplication, expansion trend behavior, staffing branch completeness, and OpenClaw contract/live checks.
7. Implement OpenClaw demonstrability: enhance `openclaw_tool.py`, add env-gated live probe script `check_openclaw_live.py`, and expose a `make` target.
8. Update docs (`README.md`, `openclaw-integration.md`, `docs/evidence/README.md`) with exact reproducible OpenClaw runbook and evidence capture requirements.
9. Run full validation sequence and update `docs/validation/test_run_report.md` with truthful pass/fail/skip states, log paths, and evidence inventory.

3. **Key technical decisions**

- Use file-specific, stateful parsers; no generic CSV parser abstraction for these reports.
- Parse quoted comma-formatted numbers with a CSV-safe tokenizer before numeric conversion.
- For `REP_S_00461.csv`, parse by column position + section state (employee block + branch block), not header-name matching.
- For `REP_S_00502.csv`, keep netting rule by `branch + customer + item`, drop only zero-net items, and robustly parse customer IDs including prefixed formats.
- For `rep_s_00150.csv`, persist branch context across repeated page headers and variable column offsets to reduce `branch=None`.
- Shared partial-period heuristic is single-source-of-truth and reused by both demand and expansion feature layers. **Primary role: exclude anomalous trailing partial months from trend/slope computation before modeling.**
- Demand boundary validity is mandatory: clamp `predicted >= 0` and `lower >= 0` in final API output. **(Defensive layer, not primary fix.)**
- Expansion trend logic is dual-layer: primary fix in feature computation plus defensive fallback in model assembly.
- Combo outputs are deduplicated by normalized sorted itemset key before `top_n` truncation.
- OpenClaw acceptance requires three proofs: contract tests, env-gated live invocation test, and captured screenshots in `docs/evidence/`.
- Encoding fix for audit 4.9 is explicit: ASCII `--` in action strings and UTF-8-safe logging stream configuration.
