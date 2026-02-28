# Project Context (Codex)

Managed by the AI Orchestrator. Codex CLI reads this file on startup.

## Project Architecture
See `orchestrator.md` in this directory for a full project summary, folder structure, architecture overview, and notes on what each component does.

## Memory

All persistent memory lives in `.orchestrator/`:
- `bugs.md` · `decisions.md` · `key_facts.md` · `issues.md` · `memory.yaml`

Check these before making architectural changes or debugging known issues.
Run `/init` to have Qwen populate them from the codebase if they are empty.

- Project objective: deliver an end-to-end AI Chief of Operations system for Conut across 5 objectives: combo optimization, branch demand forecasting, expansion feasibility, shift staffing estimation, and coffee/milkshake growth strategy.
- Grading-critical requirement: OpenClaw must be installed, callable, and evidenced (real invocation logs/screenshots/video), not only `SKILL.md` presence.
- Current state (audit 2026-02-28): pipeline runs, API endpoints respond, smoke tests pass, and `pytest` passed 30/30, but critical/major data and modeling issues remain.
- Canonical architecture/source-of-truth doc: `orchestrator.md`; check before structural changes.
- Persistent memory authority: `.orchestrator/bugs.md`, `decisions.md`, `key_facts.md`, `issues.md`, `memory.yaml`; review before debugging recurring issues.
- Data location convention: load source inputs from repo-root `Conut bakery Scaled Data/`; do not assume `data/raw/...` unless reproducibly created.
- Data ingestion decision: reports are irregular exports (page markers, repeated headers, section markers, subtotals/totals, quoted/comma numerics); use file-specific parsers, not generic CSV parsing.
- Anti-pattern: one-size-fits-all CSV parsing is unacceptable for this dataset.
- Known parser constraint: `REP_S_00461.csv` attendance must be parsed via column position + section state (header-unstable, page/employee blocks).
- Basket-mining rule (`REP_S_00502.csv`): net quantities by customer-order-item, then drop zero-net items before basket creation; do not simply drop negative rows.
- Feature requirement: `rep_s_00150.csv` must feed both expansion feasibility and coffee/milkshake growth strategy.
- Modeling guidance: scaled/anonymized values require emphasis on relative signals (rankings/ratios/patterns) over absolute magnitudes.
- Approved remediation sequence: parsers → cleaning/validation → shared utilities → model fixes → tests → OpenClaw live checks → docs/evidence → final validation.
- In-scope remediation files include parsers/cleaners/validators, demand+expansion+staffing features, demand/combo/expansion models, OpenClaw tooling, tests, docs, and validation artifacts.
- Key implementation decision: partial-period handling is primary fix for demand/expansion trend failures; exclude anomalous trailing months from slope/trend computation (do not only post-clamp).
- Defensive model guard remains required: clamp physically impossible negative forecasts after modeling.
- Branch coverage requirement: staffing and combo pipelines must include main `Conut` branch (currently missing due to parser/section carry-over issues).
- Cleaning/validation requirement: preserve usable rows but explicitly flag and quantify unattributed branch rows (e.g., `branch=None`) instead of silently dropping impact.
- Combo output requirement: deduplicate merged item-set scores after rule generation to avoid repeated top-N actions.
- OpenClaw integration decision: document concrete registration/API protocol early, but continue data/model implementation in parallel; final submission must include live proof.
- Reproducibility standard: pinned deps, executable runbook, deterministic pipeline, tests alongside code, and validation outputs under `artifacts/` and `artifacts/test_logs/`.

*(body trimmed to stay within the 400-word limit)*
