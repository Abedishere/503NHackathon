# Project Context (Claude Code)

Managed by the AI Orchestrator. Claude Code reads this file on startup.

## Project Architecture
See `orchestrator.md` in this directory for a full project summary, folder structure, architecture overview, and notes on what each component does.

## Memory

All persistent memory lives in `.orchestrator/`:
- `bugs.md` · `decisions.md` · `key_facts.md` · `issues.md` · `memory.yaml`

Check these before making architectural changes or debugging known issues.
Run `/init` to have Qwen populate them from the codebase if they are empty.

- Project objective: deliver an end-to-end Conut Chief of Operations AI system covering 5 graded objectives: combo optimization, branch-level demand forecasting, expansion feasibility, shift staffing estimation, and coffee/milkshake growth strategy.
- Grading-critical requirement: OpenClaw integration must be live and demonstrable (actual callable queries plus logs/screenshots/video evidence), not only `SKILL.md` presence.
- Canonical architecture reference: consult `orchestrator.md` before major changes; treat `.orchestrator/` (`bugs.md`, `decisions.md`, `key_facts.md`, `issues.md`, `memory.yaml`) as authoritative persistent memory.
- Raw data convention: source inputs come from repo-root `Conut bakery Scaled Data/`; do not assume `data/raw/...` unless created via reproducible copy/symlink logic.
- Parsing architecture decision: use file-specific parsers for report-style CSV exports; generic CSV parsing is an anti-pattern for this dataset.
- Parsing hazards to handle explicitly: repeated headers, page markers (`Page X of Y`), section markers, subtotal/`Total :` rows, unstable headers, and quoted/comma-formatted numerics.
- Critical parser rules:
  - `REP_S_00461.csv` (attendance): parse by column position + section state; recover main `Conut` branch coverage.
  - `REP_S_00502.csv` (sales detail): preserve branch coverage including `Conut`; basket mining must net quantities by customer-order-item, then drop zero-net items.
  - `rep_s_00150.csv` (customer orders): carry branch context across page/section boundaries; avoid silent `branch=None` loss and flag unattributed rows.
- Modeling guidance: data is scaled/anonymized; optimize for relative patterns, rankings, ratios, and directional comparisons over absolute magnitudes.
- Shared time-series fix is mandatory: exclude anomalous trailing partial periods from slope/trend computation (primary fix), then apply non-negative forecast clamping as defensive fallback.
- Trend/forecast quality requirement: avoid physically invalid negative demand and avoid global false “decreasing” labels caused by partial-month artifacts.
- Combo output requirement: deduplicate merged item-set recommendations before top-N selection so directional rule duplicates do not leak to API responses.
- Required implementation scope: parsers/cleaning/validation, shared time-series utility, demand/expansion/staffing/combo model layers, logging encoding fix, OpenClaw tool checks, docs/tests/validation artifacts.
- Tooling/repro standards: pinned dependencies, executable pipeline, clear runbook, tests alongside implementation, and explicit PDF toolchain with `make pdf`.
- Validation workflow: run pipeline, model scripts, full pytest (+ JUnit/logs), smoke/API/OpenClaw checks, and consolidated report under `artifacts/` and `artifacts/test_logs/`; if Docker unavailable, record “Docker not available — skipped.”
- Current priority: close all 9 audit issues (4.8 accepted as non-blocking if executive PDF is pre-generated), with remediation order: parser correctness -> cleaning/validation -> shared utilities -> model fixes -> tests -> OpenClaw live proof -> docs/evidence -> full validation rerun.
