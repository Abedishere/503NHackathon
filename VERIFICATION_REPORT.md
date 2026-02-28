# Conut AI Operations Agent — Verification Report

**Date:** 2026-02-28
**Type:** Re-verification against AUDIT_REPORT.md findings
**Scope:** Full pipeline re-run + targeted issue re-checks

---

## 1. Re-run Summary

| Stage | Result |
|-------|--------|
| `python scripts/run_pipeline.py` | ✅ Complete |
| `python scripts/train_models.py` | ✅ Complete — all 5 models |
| `pytest tests/ -v` | ✅ **40/40 passed** (was 30/30; 10 new tests added) |
| `python scripts/demo_smoke_test.py` | ✅ **5/5 passed** |
| `GET /health` | ✅ HTTP 200 |
| `POST /combo` | ✅ HTTP 200 |
| `POST /demand` | ✅ HTTP 200 |
| `POST /expansion` | ✅ HTTP 200 |
| `POST /staffing` | ✅ HTTP 200 |
| `POST /growth` | ✅ HTTP 200 |

---

## 2. Issue-by-Issue Status

### Issue 4.1 — OpenClaw Not Installed or Demonstrated
**Status: STILL OPEN ❌**

Nothing has changed:
- `~/.openclaw/` does not exist
- `openclaw` binary not found on `$PATH`
- `docs/evidence/` is still an empty directory
- No screenshots, logs, or video showing OpenClaw calling the API

This remains the highest grading risk. The requirement is a live, demonstrable
integration — not just a SKILL.md file.

---

### Issue 4.2 — Demand Forecasts Were Negative
**Status: RESOLVED ✅ — with one residual observation**

All four branches now forecast **positive, increasing** values. The monthly_sales
`total` column now carries correct-scale values (hundreds of millions), consistent
with the raw CSV being re-parsed without the truncation that produced the previous
values of 1–67. Trends:

| Branch | Trend | 1st Forecast Month | 1st Predicted Value |
|--------|-------|-------------------|---------------------|
| Conut | increasing | 2025-12 | ~1.59 B |
| Conut - Tyre | increasing | 2026-01 | ~1.13 B |
| Conut Jnah | increasing | 2026-01 | ~2.53 B |
| Main Street Coffee | increasing | 2026-01 | ~3.31 B |

**Residual observation — date offset for Conut:**
Conut's forecast horizon starts at `2025-12` while all other branches start at
`2026-01`. This is consistent with the partial-period exclusion logic correctly
dropping December for Conut (December value ≈ 68M vs November ≈ 1.35B, an ~20×
drop) while keeping December for the other branches where the value is within normal
range. This behavior is correct given the design, but it means Conut's "horizon"
overlaps with a month that already has partial real data — a grader may notice the
discrepancy in start dates across branches.

---

### Issue 4.3 — Staffing Missing "Conut" Branch
**Status: PRESENT IN OUTPUT — with a caveat ⚠️**

The `Conut` branch now appears in the staffing scores with shifts
`[morning, evening, night]`. However:

- **Attendance data still has zero rows for Conut.** Parsed attendance:
  `Main Street Coffee=106, Conut - Tyre=94, Conut Jnah=73` — Conut = 0.
- The Conut staffing values are **synthetic estimates** computed from the
  cross-branch median staffing ratios (via the `_estimated=True` flag in
  `staffing_features.py`).
- The API response does not surface the `_estimated` flag to the caller. A grader
  querying the `/staffing` endpoint cannot distinguish real attendance-backed data
  from median-imputed data.

**Root cause still unresolved:** `REP_S_00461.csv` does not yield any Conut rows
after parsing. The staffing output covers all 4 branches numerically, but the Conut
numbers are not grounded in actual attendance records.

**Possible reasons the parser still misses Conut attendance:**
- The Conut section of `REP_S_00461.csv` may use a different branch identifier,
  section header keyword, or page-break structure than the other three branches.
- The column-position parser may require a specific section-state trigger word that
  exists for the other branches but differs for Conut.
- There may be a different encoding or whitespace in the Conut section heading
  that the parser's string comparison does not match.

---

### Issue 4.4 — "Conut" Branch Absent from Combo Mining
**Status: STILL OPEN ❌**

`sales_detail` continues to contain rows from only 3 branches:

```
Conut Jnah:            915 rows
Main Street Coffee:    154 rows
Conut - Tyre:           53 rows
Conut (main):            0 rows
```

All 113 baskets and all combo rules are derived without any Conut main-branch
transactions. The `REP_S_00502.csv` parser has not been updated to recover Conut
rows.

**Possible reasons:**
- Same category as Issue 4.3: the Conut section in `REP_S_00502.csv` may use a
  different header structure, branch name, or section boundary than the other
  branches.
- The parser may reach a page break or section marker before the Conut records
  and terminate or reset state, silently dropping those rows.
- The branch assignment logic may rely on a keyword or column value that is
  absent or differently formatted in the Conut portion of the file.

---

### Issue 4.5 — Combo Scores Contained Duplicate Item-Sets
**Status: RESOLVED ✅**

No duplicate item-sets appear in the scores. The three action strings are now
distinct:

```
Bundle CHIMNEY THE ONE + CONUT BERRY MIX + MINI THE ORIGINAL as a combo (lift=28.25x)
Bundle ADD ICE CREAM + CHIMNEY THE ORIGINAL + STRAWBERRIES (R) as a combo (lift=25.11x)
Bundle CHIMNEY THE ONE + CONUT BERRY MIX + CONUT BITES as a combo (lift=22.6x)
```

Deduplication check across all scores: **0 duplicate item-sets found.**

---

### Issue 4.6 — Customer Orders: 89 Records With No Branch
**Status: RESOLVED ✅**

`customer_orders` now has `branch=None: 0 of 539`. All four branches are present:
`['Conut - Tyre', 'Conut', 'Conut Jnah', 'Main Street Coffee']`

---

### Issue 4.7 — All Branches Labeled "Decreasing" in Expansion
**Status: RESOLVED ✅**

All four branches now show `revenue_trend: increasing`. Feasibility scores:

| Branch | Score | Trend |
|--------|-------|-------|
| Conut Jnah | 0.792 | increasing |
| Main Street Coffee | 0.731 | increasing |
| Conut | 0.586 | increasing |
| Conut - Tyre | 0.563 | increasing |

---

### Issue 4.8 — weasyprint Fails on Windows
**Status: STILL FAILING ⚠️ (accepted as non-blocking)**

`make pdf` still fails with the GTK/gobject library error. `docs/executive_brief.pdf`
exists as a pre-generated artifact. Per the CLAUDE.md note, this is accepted as
non-blocking if the PDF is pre-generated.

---

### Issue 4.9 — Em Dash Garbled in Log Output
**Status: STILL PRESENT ⚠️**

The em dash character (`—`) still renders as a garbled replacement character in
Windows terminal/log output:

```
repr: 'Review Conut \ufffd demand trending down'
```

The API JSON responses are unaffected. The garbling is isolated to console and
log-file output in Windows environments where the shell code page is not UTF-8.

**Possible reasons:**
- The Python logger does not set `encoding='utf-8'` on its stream handler, so
  Windows' default code page (CP1252/CP850) mangles multi-byte characters.
- The em dash literal in the source string is written as `—` (U+2014) rather than
  an ASCII approximation (`--` or `-`), which would survive any code page.

---

## 3. New Issues Discovered During Re-verification

### NEW ISSUE A — Staffing: Conut Data Is Synthetic (Not Disclosed to API Consumers)
**Severity: MODERATE**

As noted in Issue 4.3 above, the Conut staffing values are median-imputed. The
staffing model internally marks these rows with `_estimated=True` but the API
response schema does not expose this flag. Any grader who inspects the `/staffing`
response will not know the Conut numbers are estimated from other branches rather
than derived from Conut's own attendance records.

**Possible reasons this was not surfaced:**
- The `OperationsResponse` Pydantic schema does not include a field for per-branch
  data quality flags.
- The shift-level scores dict only carries `shift`, `current_staff`,
  `recommended_staff`, `gap`, and `avg_hours_per_shift`.

---

### NEW ISSUE B — Demand Forecast: Conut First Month Is 2025-12, Others Are 2026-01
**Severity: MINOR**

Conut's partial-period exclusion leaves November as its last training point, so
its forecast starts at December 2025 — a month that has already partially occurred.
The other branches (which do not have an anomalous December) include December in
training and forecast from January 2026 onward. This inconsistency in horizon
alignment could confuse a grader comparing branch forecasts side-by-side.

---

## 4. Updated Issue Status Table

| # | Issue | Previous Status | Current Status |
|---|-------|----------------|----------------|
| 4.1 | OpenClaw not installed / no demo evidence | ❌ OPEN | ❌ STILL OPEN |
| 4.2 | Demand forecasts all negative | ❌ OPEN | ✅ RESOLVED |
| 4.3 | Staffing missing Conut branch | ❌ OPEN | ⚠️ OUTPUT PRESENT (synthetic) |
| 4.4 | Combo missing Conut branch (sales_detail) | ❌ OPEN | ❌ STILL OPEN |
| 4.5 | Combo duplicate item-sets | ⚠️ OPEN | ✅ RESOLVED |
| 4.6 | Customer orders 89 rows branch=None | ⚠️ OPEN | ✅ RESOLVED |
| 4.7 | All expansion branches labeled "decreasing" | ⚠️ OPEN | ✅ RESOLVED |
| 4.8 | weasyprint fails on Windows | ⚠️ MINOR | ⚠️ STILL FAILING (non-blocking) |
| 4.9 | Em dash garbled in logs | ⚠️ MINOR | ⚠️ STILL PRESENT |
| NEW A | Staffing Conut estimates not disclosed | — | ⚠️ NEW |
| NEW B | Demand forecast date offset (Conut) | — | ⚠️ NEW |

---

## 5. Test Coverage Update

Tests increased from **30 to 40**. The 10 new tests added since the audit:

| Test | What It Checks |
|------|---------------|
| `test_no_duplicate_itemsets` | Combo scores have no repeated item-sets |
| `test_actions_not_duplicated` | Combo actions list has no identical strings |
| `test_forecast_no_negative_predictions` | All forecast `predicted` values ≥ 0 |
| `test_monthly_sales_values_correct_scale` | Monthly sales not all near-zero (≥ 1000) |
| `test_not_all_branches_decreasing` | Expansion: at least one branch labeled "increasing" |
| `test_four_branches_analyzed` | Expansion: exactly 4 branches in scores |
| `test_customer_orders_all_branches_present` | customer_orders has no branch=None |
| `test_all_four_branches_covered` | Staffing: 4 branches in output |
| `test_customer_orders_all_branches_attributed` | customer_orders branches = 4 known names |
| (ingestion test) | Monthly sales totals not truncated |

---

## 6. Deliverables Status (Final)

| Deliverable | Status | Notes |
|-------------|--------|-------|
| End-to-end pipeline | ✅ | Runs clean |
| Pinned dependencies | ✅ | `requirements.txt` complete |
| 5 business objectives — API | ✅ | All 6 endpoints respond HTTP 200 |
| 40 tests passing | ✅ | `40/40 passed` |
| OpenClaw SKILL.md | ✅ | Present with correct frontmatter |
| OpenClaw live integration | ❌ | Not installed; no evidence |
| Demo evidence (screenshots/video) | ❌ | `docs/evidence/` empty |
| README | ✅ | Complete |
| Executive brief PDF | ✅ | Pre-generated; `make pdf` fails |
| GitHub repo (public) | ⚠️ | Cannot verify locally |

---

## 7. Remaining Open Actions Before Submission

| Priority | Action |
|----------|--------|
| **1 — CRITICAL** | Install OpenClaw, install the skill, run at least one live query per objective, capture screenshots into `docs/evidence/` |
| **2 — MAJOR** | Fix `REP_S_00502.csv` parser to recover Conut main-branch sales rows so combo mining uses all 4 branches |
| **3 — MODERATE** | Expose `_estimated` flag in staffing API response so graders can distinguish real vs. imputed Conut data |
| **4 — MINOR** | Fix log encoding (UTF-8 stream handler) to eliminate garbled em dash output |
| **5 — MINOR** | Align demand forecast start months across branches (consider always forecasting from `max(last_date)+1` relative to today) |

---

*Report generated automatically by Claude Code on 2026-02-28.*
