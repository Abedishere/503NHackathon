# Conut AI Operations Agent — Full Audit Report

**Date:** 2026-02-28
**Auditor:** Claude Code (automated run + code inspection)
**Scope:** End-to-end evaluation against the AUB AI Engineering Hackathon requirements

---

## 1. Executive Summary

The system is substantially complete. The data pipeline runs cleanly, all five business-objective
models produce output, the FastAPI server responds correctly on all six endpoints, and 30/30 pytest
tests pass. However, several issues — ranging from a grading-critical gap to moderate data and logic
problems — are identified below and require attention before submission.

---

## 2. Test Execution Results

| Stage | Command | Result |
|-------|---------|--------|
| Data pipeline | `python scripts/run_pipeline.py` | ✅ Completed — 9 reports parsed, artifacts saved |
| Model training | `python scripts/train_models.py` | ✅ All 5 models ran, JSON artifacts written |
| Unit + integration tests | `pytest tests/ -v` | ✅ **30/30 passed** in 2.70 s |
| Smoke test | `python scripts/demo_smoke_test.py` | ✅ **5/5 passed** |
| API health | `GET /health` | ✅ HTTP 200 `{"status":"ok","version":"1.0.0"}` |
| API combo | `POST /combo` | ✅ HTTP 200, correct schema |
| API demand | `POST /demand` | ✅ HTTP 200, correct schema |
| API expansion | `POST /expansion` | ✅ HTTP 200, correct schema |
| API staffing | `POST /staffing` | ✅ HTTP 200, correct schema |
| API growth | `POST /growth` | ✅ HTTP 200, correct schema |
| Docker | `make docker-build / docker-run` | ⚠️ Skipped — Docker Desktop not running (logged) |
| PDF generation | `make pdf` | ❌ Fails — weasyprint cannot load `libgobject-2.0-0` on Windows |

---

## 3. Deliverables Checklist vs. Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| End-to-end pipeline | ✅ | ingest → clean → validate → artifacts |
| Pinned dependencies (`requirements.txt`) | ✅ | All core packages version-pinned |
| Operational AI component (5 objectives) | ✅ | All 5 endpoints live |
| OpenClaw SKILL.md defined | ✅ | `skills/conut-ops/SKILL.md` with frontmatter + all endpoints |
| OpenClaw installed and callable on this machine | ❌ | `~/.openclaw/` does not exist; binary not found |
| Live OpenClaw demo evidence (screenshots / video) | ❌ | `docs/evidence/` directory is empty |
| Public GitHub repository | ⚠️ | Cannot verify from local audit — must confirm manually |
| README (problem, approach, how to run, results) | ✅ | Present and complete |
| Executive brief (max 2 pages, PDF) | ✅ | `docs/executive_brief.pdf` exists |

---

## 4. Issues by Severity

---

### 4.1 CRITICAL — OpenClaw Not Installed or Demonstrated

**What was found:**
- `~/.openclaw/` directory does not exist on this machine.
- The `openclaw` binary is not present on `$PATH`.
- The `artifacts/test_logs/openclaw_checks.log` records only that `SKILL.md` was *generated*,
  not that OpenClaw ever called the API.
- `tests/test_openclaw_integration.py` passes by checking that the SKILL.md file contains
  the right text strings — it makes no live HTTP call to an OpenClaw gateway.
- `docs/evidence/` is an empty directory; there are no screenshots or video.

**Why this matters:**
The assignment grading criteria state explicitly:

> *"Your grade includes whether this integration works in practice, not only in theory."*
> *"Demo evidence: screenshots or short video / OpenClaw invoking your solution."*

**Possible reasons the integration has not been demonstrated:**
- OpenClaw may require a specific OS/architecture and has not yet been installed on this machine.
- The team may have planned to do the live demo at a later stage but has not reached it.
- The OpenClaw binary may be installed under a different path not on `$PATH`.
- The team may be relying on a remote machine or a different user account for the demo.
- The SKILL.md + API combination may have been validated on a separate machine whose
  evidence (screenshots) was not copied into this repository.

**What is missing from the repository:**
- Any log line showing `GET /combo` (or similar) initiated by an OpenClaw process.
- At least one screenshot showing OpenClaw invoking a query and receiving a response.
- Optionally: a webhook push log showing the reverse direction.

---

### 4.2 MAJOR — Demand Forecasts Produce Negative Predicted Values

**What was found:**
All four branches receive negative demand forecasts:

| Branch | Jan 2026 | Feb 2026 | Mar 2026 |
|--------|----------|----------|----------|
| Conut | −245.7 | −421.4 | −597.1 |
| Conut - Tyre | −233.5 | −373.0 | −512.5 |
| Conut Jnah | −557.7 | −1,251.8 | −1,945.9 |
| Main Street Coffee | −69.0 | −203.5 | −338.0 |

The underlying raw monthly sales data shows this pattern per branch:

| Branch | Aug | Sep | Oct | Nov | Dec |
|--------|-----|-----|-----|-----|-----|
| Conut | 554 | 784 | 1 | 1 | 67 |
| Conut - Tyre | 477 | 444 | 2 | 1 | 1 |
| Conut Jnah | 363 | 714 | 785 | 947 | 2 |
| Main Street Coffee | — | 145 | 920 | 1 | 3 |

The exponential smoothing model (with additive trend) fits the full sequence including the steep
drop in the final months, then extrapolates that negative slope forward.

**Why this matters:**
Demand cannot be negative. Presenting negative forecasts to a grader signals that the model
is not functioning correctly and undermines the credibility of the entire demand-forecasting
objective.

**Possible reasons for the severe month-end drops:**
- The report export was generated mid-period; the last one or two months are incomplete
  (only partial data was available at export time), making those months look artificially low.
- The `REP_S_00334_1_SMRY.csv` parser may be mis-assigning month totals — for instance,
  reading a subtotal row as a monthly row, or conflating multiple periods.
- The `total` column in the monthly sales table may represent a different unit than revenue
  (e.g., transaction count, or a scaled/transformed metric) that should not be modeled with
  an additive trend.
- The data scaling described in the assignment brief may have introduced non-linear distortions
  that cause the last-period values to be near zero for reasons unrelated to true business volume.
- The exponential smoothing model with `trend="add"` and `initialization_method="estimated"`
  may be over-fitting a short sequence (4–5 points) and producing unbounded extrapolation.

**Observable consequence:**
All four branches are labeled as `"trend": "decreasing"` and all actions say
"demand trending down, optimize costs" — regardless of Conut Jnah, which clearly grew from
363 → 714 → 785 → 947 in the three months before December.

---

### 4.3 MAJOR — "Conut" Main Branch Absent from Staffing Output

**What was found:**
The staffing endpoint returns results for 3 branches only:
- Conut - Tyre
- Conut Jnah
- Main Street Coffee

The main **"Conut"** branch — which appears in monthly_sales, division_summary, customer_orders,
and item_sales — is entirely absent from the staffing scores.

Root cause: the attendance dataset (`REP_S_00461.csv`) parses into records for only three branches:

```
Main Street Coffee    106
Conut - Tyre           94
Conut Jnah             73
```

The main "Conut" branch has zero attendance rows after parsing.

**Possible reasons:**
- The attendance report may use a different name for the main branch (e.g., a different
  spelling, abbreviation, or code) that the parser does not map to `"Conut"`.
- The CLAUDE.md notes that `REP_S_00461.csv` is "positional/header-unstable with employee/page
  sections" and must be "parsed by column position + section state, not header names." The
  parser may be missing a section of the file that corresponds to the main branch.
- The main branch's employee records may appear in a different part of the file (e.g., before
  a page break or under a different section header) that the parser skips.
- The 38 rows that were dropped during cleaning (311 raw → 273 after clean) may include the
  Conut main branch records.

**Observable consequence:**
Any staffing question about the main "Conut" branch returns no data. The `data.branches_analyzed`
field in the staffing response reports `3`, not `4`.

---

### 4.4 MAJOR — Combo Optimizer: "Conut" Main Branch Absent from Basket Construction

**What was found:**
`sales_detail` — which is the sole input to basket construction — contains rows from only 3 branches:

```
Conut Jnah            890 rows
Main Street Coffee    146 rows
Conut - Tyre           53 rows
```

The main "Conut" branch has zero rows in `sales_detail`, meaning all combo recommendations
are derived entirely from the other three branches. Only 113 baskets were constructed from
1,089 cleaned rows.

**Possible reasons:**
- `REP_S_00502.csv` (sales by customer in detail) may contain Conut main branch records under
  a different branch name or section header that the parser does not recognize.
- The parser for `REP_S_00502.csv` may terminate early or skip pages that cover the main branch.
- The branch name in the raw file may use a different encoding or trailing whitespace that
  prevents matching.
- The CLAUDE.md notes that `REP_S_00502.csv` uses "net quantities by customer-order-item"
  logic; it is possible that after netting, Conut main branch items all zero out and are dropped.

**Observable consequence:**
Combo recommendations for a grader asking about the main Conut branch are based on zero data.
The `data.total_transactions` in the combo response is 113, not the full dataset.

---

### 4.5 MODERATE — Combo Scores Contain Duplicate Entries

**What was found:**
The combo endpoint returns `scores` where the same item-set appears multiple times with
different confidence values:

```
items: [CHIMNEY THE ONE, CONUT BERRY MIX, MINI THE ORIGINAL]  confidence: 0.5,  lift: 28.25
items: [CHIMNEY THE ONE, CONUT BERRY MIX, MINI THE ORIGINAL]  confidence: 1.0,  lift: 28.25

items: [ADD ICE CREAM, CHIMNEY THE ORIGINAL, STRAWBERRIES (R)]  confidence: 0.6667, lift: 25.11
items: [ADD ICE CREAM, CHIMNEY THE ORIGINAL, STRAWBERRIES (R)]  confidence: 0.6667, lift: 25.11
```

Association rule mining produces both A → B and B → A as separate rules from the same
frequent itemset. The current code merges antecedents and consequents into a single `items`
list, which makes the duplicate rules look identical to the API consumer.

**Possible reasons:**
- The code does not deduplicate rules by the merged (sorted) item-set before returning scores.
- The `top_n` parameter limits the number of rules before deduplication, causing visible
  duplicates within the returned list.
- The sorting by lift is applied to the raw rules frame, which ranks directional duplicates
  adjacent to each other, making them visible in the top results.

**Observable consequence:**
When `top_n=3`, the first two items in `actions` are identical:
```
"Bundle CONUT BERRY MIX + CHIMNEY THE ONE + MINI THE ORIGINAL as a combo (lift=28.25x)"
"Bundle CONUT BERRY MIX + CHIMNEY THE ONE + MINI THE ORIGINAL as a combo (lift=28.25x)"
```

---

### 4.6 MODERATE — Customer Orders: 89/539 Records Have No Branch Assignment

**What was found:**
The `customer_orders` table contains 89 rows (16.5% of records) where `branch` is `None`.
These records are silently excluded from the expansion feasibility calculation and the
`rep_s_00150.csv` signals integration.

**Possible reasons:**
- The `rep_s_00150.csv` parser may fail to carry a branch header forward across page breaks
  or section boundaries.
- Some customer records in the raw file may be aggregate-level (not tied to a specific branch),
  and the parser does not distinguish these from per-branch rows.
- The branch detection logic may rely on a specific column position or keyword that is absent
  for some sections of the file.

**Observable consequence:**
The `expansion_feasibility` scores for branches (especially Conut - Tyre, which shows
`repeat_rate: 0.0` and `num_customers` that may be under-counted) could be skewed because
a significant share of customers cannot be attributed to a branch. The README claims 4 branches
are analyzed; the data supports this, but 16.5% of the customer base is unattributed.

---

### 4.7 MODERATE — Expansion Feasibility: All Branches Show "Decreasing" Revenue Trend

**What was found:**
The expansion output labels all four branches with `"revenue_trend": "decreasing"`:

```
Conut Jnah      score: 0.67   trend: decreasing
Conut           score: 0.642  trend: decreasing
Main Street Coffee  score: 0.341  trend: decreasing
Conut - Tyre    score: 0.082  trend: decreasing
```

Conut Jnah shows sales of 363 → 714 → 785 → 947 for Aug–Nov 2025 — a clear uptrend —
before a near-zero December value collapses the slope calculation.

**Possible reasons:**
- Same root cause as Issue 4.2: the near-zero December values distort the linear slope used
  to determine the trend label.
- The `revenue_trend` flag may be derived from the same raw data that affects demand
  forecasting, meaning the December anomaly propagates into the expansion scoring.

**Observable consequence:**
Every branch is described as "decreasing" and no branch qualifies as a growth candidate
from a trend perspective, even though Conut Jnah was clearly growing through November.

---

### 4.8 MINOR — weasyprint Fails on Windows (`make pdf`)

**What was found:**
Running `make pdf` fails with:

```
OSError: cannot load library 'libgobject-2.0-0': error 0x7e
```

weasyprint requires GTK/GObject runtime libraries which are not installed on this Windows machine.

**Possible reasons:**
- weasyprint on Windows requires GTK3 to be installed separately via MSYS2 or a standalone
  installer; this step is not documented in the README or requirements.
- The PDF was generated on a different machine (Linux/macOS) and committed directly; the
  `make pdf` target was never tested on Windows.

**Observable consequence:**
`docs/executive_brief.pdf` already exists (pre-generated), so graders who simply open the
file are not affected. However, a grader who attempts to reproduce the PDF from source using
`make pdf` will see a failure. The `make all` target does not call `make pdf`, so this does
not block the main pipeline.

---

### 4.9 MINOR — Log Encoding Artifact (Em Dash Garbled in Train Log)

**What was found:**
The `artifacts/test_logs/train.log` file (and train script stdout) shows:

```
Review Conut 🇦 demand trending down
```

The em dash character `—` is being rendered as a garbled byte sequence in the Windows console
code page. The API JSON responses themselves encode the character correctly.

**Possible reasons:**
- The Python logging handler writes to stdout without specifying `encoding='utf-8'`, allowing
  the Windows default code page (e.g., CP1252 or CP850) to mangle multi-byte characters.
- The em dash is used as a literal string in `demand_forecaster.py` action generation; it
  renders correctly in environments with UTF-8 terminals but not in Windows cmd/PowerShell.

**Observable consequence:**
Log files and console output contain garbled characters, which could look unprofessional
if shown during a live demo. API responses are not affected.

---

## 5. Data Quality Observations

| Observation | Affected Report | Implication |
|-------------|----------------|-------------|
| Monthly sales values drop to 1–3 in last 1–2 months | `REP_S_00334_1_SMRY.csv` | Invalidates demand trend direction for all branches |
| "Conut" main branch absent from attendance | `REP_S_00461.csv` | Staffing covers only 3 of 4 branches |
| "Conut" main branch absent from sales detail | `REP_S_00502.csv` | Combo mining covers only 3 of 4 branches |
| 89/539 customer_orders have `branch=None` | `rep_s_00150.csv` | 16.5% of customer data unattributed |
| `avg_menu_sales` has 2 rows with `branch=None` | `rep_s_00435_SMRY.csv` | Aggregate rows not separated from branch rows |
| item_sales `total_amount` values look scaled/near-zero | `rep_s_00191_SMRY.csv` | Amounts not comparable to monthly_sales totals |

---

## 6. Requirement-by-Requirement Assessment

### Business Objectives

| Objective | Implemented | Data Complete | Output Correct |
|-----------|-------------|---------------|----------------|
| 1. Combo Optimization | ✅ Apriori + rules | ⚠️ Missing "Conut" branch | ⚠️ Duplicate rules in top-N |
| 2. Demand Forecasting | ✅ Exponential smoothing | ⚠️ Last-period anomaly | ❌ All forecasts negative |
| 3. Expansion Feasibility | ✅ Composite scoring | ⚠️ 16.5% unattributed customers | ⚠️ All trends labeled "decreasing" |
| 4. Shift Staffing | ✅ Demand/attendance ratio | ❌ "Conut" branch missing | ⚠️ Only 3/4 branches covered |
| 5. Coffee & Milkshake Growth | ✅ Category + cross-sell | ✅ Uses item_sales + combos | ✅ Plausible results |

### Technical Requirements

| Requirement | Status |
|-------------|--------|
| End-to-end pipeline executable | ✅ |
| Reproducibility (pinned deps, run instructions) | ✅ |
| Operational AI component answering all 5 objectives | ✅ (with caveats above) |
| OpenClaw integration: SKILL.md defined | ✅ |
| OpenClaw integration: live / demonstrable | ❌ |

### Deliverables

| Deliverable | Status |
|-------------|--------|
| Public GitHub repository | ⚠️ Cannot verify locally |
| README (problem, approach, how to run, results) | ✅ |
| Executive brief PDF (≤2 pages) | ✅ Pre-generated; `make pdf` fails |
| Demo evidence (screenshots / video) | ❌ `docs/evidence/` is empty |
| OpenClaw invoking the solution | ❌ No evidence |

---

## 7. Summary of Open Items by Priority

| # | Severity | Item |
|---|----------|------|
| 1 | CRITICAL | OpenClaw not installed; no live integration demonstrated; no screenshots |
| 2 | MAJOR | Demand forecasts are all negative — model output is physically invalid |
| 3 | MAJOR | "Conut" main branch absent from staffing (attendance parser) |
| 4 | MAJOR | "Conut" main branch absent from combo mining (sales_detail parser) |
| 5 | MODERATE | Combo scores contain duplicate item-set entries in top-N output |
| 6 | MODERATE | 89 customer records have no branch; affects expansion and growth signals |
| 7 | MODERATE | All branches labeled "decreasing" in expansion due to same data anomaly |
| 8 | MINOR | `make pdf` fails on Windows (weasyprint GTK dependency missing) |
| 9 | MINOR | Em dash garbled in log output on Windows code page |

---

*Report generated automatically by Claude Code on 2026-02-28.*
