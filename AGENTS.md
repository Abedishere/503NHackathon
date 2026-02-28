# Project Context (Codex)

Managed by the AI Orchestrator. Codex CLI reads this file on startup.

## Project Architecture
See `orchestrator.md` in this directory for a full project summary, folder structure, architecture overview, and notes on what each component does.

## Memory

All persistent memory lives in `.orchestrator/`:
- `bugs.md` · `decisions.md` · `key_facts.md` · `issues.md` · `memory.yaml`

Check these before making architectural changes or debugging known issues.
Run `/init` to have Qwen populate them from the codebase if they are empty.

- Project goal: deliver an end-to-end AI Chief of Operations system for Conut that answers 5 business objectives: combo optimization, branch-level demand forecasting, expansion feasibility, shift staffing estimation, and coffee/milkshake growth strategy.
- Mandatory integration: OpenClaw integration is required for grading and must be demonstrably functional (not theoretical). The system must expose callable operational queries (forecasting, staffing, combos, growth prompts).
- Data location convention: read from existing repo-root folder `Conut bakery Scaled Data/`. Do not assume `data/raw/...` unless created via explicit reproducible target (copy/symlink).
- Data reality: all source CSVs are report-style exports with irregular structure (page markers, repeated headers, inline section markers, subtotal/total rows, comma-formatted numerics). Generic CSV loading is an anti-pattern.
- Parsing decision: implement per-report parsers (file-specific cleaning logic), then normalize to canonical tables. Treat ingestion/cleaning as highest-risk/highest-effort.
- Known file-specific constraint: `REP_S_00461.csv` (attendance) is positional/no stable headers, includes page breaks and employee sections; parse by column position and section-state, not header names.
- Basket mining rule for `REP_S_00502.csv`: handle returns/cancellations by netting quantities per customer-order-item; drop zero-net items before basket construction. Do not simply remove negative rows.
- Modeling guidance: because numeric values are scaled/anonymized, optimize for patterns, ratios, relative comparisons, and ranking rather than absolute business magnitudes.
- `rep_s_00150.csv` usage: include in both expansion feasibility (customer density/retention/frequency signals) and coffee/milkshake growth strategy (repeat behavior and spend segmentation).
- Sequencing decision: OpenClaw API/registration mechanism must be researched early and documented concretely (actual protocol/registration path), but this must not block data + modeling steps.
- Engineering requirement: reproducibility is first-class (`README` runbook, pinned dependencies, executable pipeline, validation-ready repo structure).
- Testing convention: write tests alongside implementation (parsers, feature logic, service contracts), not as a final phase.
- Build/tooling correction: add explicit PDF toolchain for executive brief (e.g., `pandoc` or `weasyprint`) and `make pdf` target.
- Delivery expectations: public GitHub repo, clear README (problem/architecture/run/results), executive brief PDF (<=2 pages), and demo evidence (screenshots/video showing OpenClaw invoking system).
- Current state note: planning and risk corrections established; implementation should now follow corrected sequencing and constraints above.
