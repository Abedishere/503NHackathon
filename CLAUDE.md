# Project Context (Claude Code)

Managed by the AI Orchestrator. Claude Code reads this file on startup.

## Project Architecture
See `orchestrator.md` in this directory for a full project summary, folder structure, architecture overview, and notes on what each component does.

## Memory

All persistent memory lives in `.orchestrator/`:
- `bugs.md` · `decisions.md` · `key_facts.md` · `issues.md` · `memory.yaml`

Check these before making architectural changes or debugging known issues.
Run `/init` to have Qwen populate them from the codebase if they are empty.

- Project goal: deliver an end-to-end **Chief of Operations AI agent** for Conut’s scaled operational dataset, covering five required objectives: combo optimization, branch-level demand forecasting, expansion feasibility, shift staffing estimation, and coffee/milkshake growth strategy.
- Mandatory constraint: **OpenClaw integration must work in practice** (not conceptual). Treat integration as a graded deliverable equal to modeling quality.
- Data location convention: source files currently exist at repo root in `Conut bakery Scaled Data/`. Do not hardcode a different default path (e.g., `data/raw/...`) unless created via an explicit reproducible target.
- Parsing strategy decision: these CSVs are **report exports**, not clean tabular files. Use **per-report parsers** (file-specific logic), not one generic parser.
- Known parsing hazards to handle explicitly:
  - Repeated headers and page markers (`Page X of Y`) mid-file.
  - Inline section markers (branch/customer/employee blocks).
  - Subtotal/`Total :` rows mixed with records.
  - Quoted comma-formatted numerics (e.g., `"1,251,486.48"`).
- Critical file note: `REP_S_00461.csv` (attendance) is positional and headerless with punch-in/out pairs plus page/section breaks; infer schema by column positions and block context.
- Basket mining rule for `REP_S_00502.csv`: handle cancellations/returns by **netting quantities per customer-order-item**, then drop zero-net lines before basket construction. Do not simply delete negative rows.
- Scope mapping decision: include `rep_s_00150.csv` features (recency/frequency/spend/order counts) in both:
  - expansion feasibility signals, and
  - coffee/milkshake growth segmentation.
- Delivery/reproducibility conventions:
  - Build tests in parallel with implementation, not as a final phase.
  - Add missing package `__init__.py` files where needed.
  - Keep binary artifacts out mandatory repo file list; generate PDF via tooling and capture demo evidence manually.
- Toolchain decision: define explicit PDF generation path (`pandoc` or `weasyprint`) and expose `make pdf`.
- Sequencing decision: research and lock OpenClaw contract early, but do **not** block core data/model pipeline work (ingestion through analytics) on integration discovery.
- Docker sequencing: create containerization after core runnable code paths are established, then freeze for reproducibility.
