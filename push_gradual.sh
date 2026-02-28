#!/usr/bin/env bash
# =============================================================
# push_gradual.sh
# Pushes files to GitHub in logical groups with timed delays.
#
# Timing: 63 non-data files × 114 s/file ≈ 7200 s = 2 hours
# Data CSVs are pushed at the end with no delay.
#
# Pre-requisites:
#   • Run from the repo root directory
#   • Target GitHub repo must be EMPTY
#   • Git credentials configured (HTTPS token or SSH key)
# =============================================================
set -euo pipefail

REMOTE_URL="https://github.com/Abedishere/503NHackathon.git"
SECS_PER_FILE=114   # 7200 s / 63 non-data files

echo ""
echo "============================================================"
echo "  Gradual push — Conut AI Hackathon"
echo "  Remote  : $REMOTE_URL"
echo "  Timing  : $SECS_PER_FILE s per file  (~2 h total)"
echo "  Started : $(date '+%H:%M:%S')"
echo "============================================================"
echo ""

# ── re-init clean local git ──────────────────────────────────
echo "[$(date '+%H:%M:%S')] Re-initialising git …"
rm -rf .git
git init
git checkout -b main 2>/dev/null || git symbolic-ref HEAD refs/heads/main
BRANCH=$(git symbolic-ref --short HEAD)
git remote add origin "$REMOTE_URL"
echo "[$(date '+%H:%M:%S')] Ready on branch: $BRANCH"
echo ""

FIRST_PUSH=true

# ── helper ───────────────────────────────────────────────────
# push_group <delay_secs> <message> <file1> [file2 …]
#   delay_secs = 0  →  no sleep (used for data files)
push_group() {
    local delay_secs="$1"
    local message="$2"
    shift 2
    local files=("$@")
    local n="${#files[@]}"

    echo "[$(date '+%H:%M:%S')] ── $message  ($n file(s)) ──"
    git add -- "${files[@]}"
    git commit -m "$message"

    if [ "$FIRST_PUSH" = true ]; then
        git push -u origin "$BRANCH"
        FIRST_PUSH=false
    else
        git push origin "$BRANCH"
    fi
    echo "[$(date '+%H:%M:%S')]    ✓ Pushed."

    if [ "$delay_secs" -gt 0 ]; then
        echo "[$(date '+%H:%M:%S')]    Sleeping ${delay_secs}s …"
        sleep "$delay_secs"
    fi
    echo ""
}

# Convenience: compute delay automatically from file count
# Usage: push_auto "message" file1 file2 …
push_auto() {
    local message="$1"
    shift
    local files=("$@")
    local n="${#files[@]}"
    local secs=$(( n * SECS_PER_FILE ))
    push_group "$secs" "$message" "${files[@]}"
}

# ════════════════════════════════════════════════════════════
#  GROUPS  (delay computed automatically per file count)
# ════════════════════════════════════════════════════════════

# 1 · Bootstrap  (4 files → 456 s)
push_auto "Initial project setup" \
    .gitignore \
    .env.example \
    pyproject.toml \
    requirements.txt

# 2 · Build & readme  (2 files → 228 s)
push_auto "Add Makefile and README" \
    Makefile \
    README.md

# 3 · Documentation  (3 files → 342 s)
push_auto "Add project documentation" \
    CONUT_AI_ENGINEERING_HACKATHON.md \
    docs/architecture.md \
    docs/openclaw-integration.md

# 4 · More docs  (2 files → 228 s)
push_auto "Add executive brief and orchestrator notes" \
    docs/executive_brief.html \
    orchestrator.md

# 5 · Agent config  (3 files → 342 s)
push_auto "Add agent configuration and skills" \
    CLAUDE.md \
    AGENTS.md \
    skills/conut-ops/SKILL.md

# 6 · Orchestrator memory  (5 files → 570 s)
push_auto "Add orchestrator memory files" \
    .orchestrator/bugs.md \
    .orchestrator/decisions.md \
    .orchestrator/key_facts.md \
    .orchestrator/issues.md \
    .orchestrator/plan.md

# 7 · Orchestrator sessions  (2 files → 228 s)
push_auto "Add orchestrator session logs" \
    ".orchestrator/sessions/7d6447f1.json" \
    ".orchestrator/transcript_20260228_095859.log"

# 8 · Source init  (2 files → 228 s)
push_auto "Bootstrap source package" \
    src/__init__.py \
    src/config.py

# 9 · Utilities  (2 files → 228 s)
push_auto "Add utility modules" \
    src/utils/__init__.py \
    src/utils/logging.py

# 10 · Data layer  (4 files → 456 s)
push_auto "Add data ingestion and cleaning pipeline" \
    src/data/__init__.py \
    src/data/ingest_reports.py \
    src/data/clean_reports.py \
    src/data/validate.py

# 11 · Feature engineering part 1  (3 files → 342 s)
push_auto "Add demand and combo feature engineering" \
    src/features/__init__.py \
    src/features/demand_features.py \
    src/features/combo_features.py

# 12 · Feature engineering part 2  (3 files → 342 s)
push_auto "Add staffing, expansion and growth features" \
    src/features/staffing_features.py \
    src/features/expansion_features.py \
    src/features/growth_features.py

# 13 · Models part 1  (3 files → 342 s)
push_auto "Add demand forecaster and combo optimizer" \
    src/models/__init__.py \
    src/models/demand_forecaster.py \
    src/models/combo_optimizer.py

# 14 · Models part 2  (3 files → 342 s)
push_auto "Add staffing, expansion and growth models" \
    src/models/staffing_estimator.py \
    src/models/expansion_feasibility.py \
    src/models/growth_strategy.py

# 15 · Integrations  (2 files → 228 s)
push_auto "Add OpenClaw integration" \
    src/integrations/__init__.py \
    src/integrations/openclaw_tool.py

# 16 · Services  (2 files → 228 s)
push_auto "Add operations agent service" \
    src/services/__init__.py \
    src/services/operations_agent.py

# 17 · API layer  (3 files → 342 s)
push_auto "Add FastAPI application layer" \
    src/api/__init__.py \
    src/api/schemas.py \
    src/api/main.py

# 18 · Tests part 1  (3 files → 342 s)
push_auto "Add ingestion and forecasting tests" \
    tests/__init__.py \
    tests/test_ingestion_cleaning.py \
    tests/test_demand_forecaster.py

# 19 · Tests part 2  (3 files → 342 s)
push_auto "Add combo, staffing and expansion tests" \
    tests/test_combo_optimizer.py \
    tests/test_staffing_estimator.py \
    tests/test_expansion_feasibility.py

# 20 · Tests part 3  (3 files → 342 s)
push_auto "Add growth strategy and API tests" \
    tests/test_growth_strategy.py \
    tests/test_api_endpoints.py \
    tests/test_openclaw_integration.py

# 21 · Scripts  (4 files → 456 s)
push_auto "Add pipeline and training scripts" \
    scripts/run_pipeline.py \
    scripts/train_models.py \
    scripts/generate_recommendations.py \
    scripts/demo_smoke_test.py

# 22 · Docker  (2 files → 228 s)
push_auto "Add Docker configuration" \
    docker/Dockerfile.api \
    docker/docker-compose.yml

# ════════════════════════════════════════════════════════════
#  DATA FILES  —  all at once, no delay
# ════════════════════════════════════════════════════════════
push_group 0 "Add Conut bakery scaled dataset" \
    "Conut bakery Scaled Data/REP_S_00136_SMRY.csv" \
    "Conut bakery Scaled Data/REP_S_00194_SMRY.csv" \
    "Conut bakery Scaled Data/REP_S_00461.csv" \
    "Conut bakery Scaled Data/REP_S_00502.csv" \
    "Conut bakery Scaled Data/rep_s_00150.csv" \
    "Conut bakery Scaled Data/rep_s_00191_SMRY.csv" \
    "Conut bakery Scaled Data/rep_s_00334_1_SMRY.csv" \
    "Conut bakery Scaled Data/rep_s_00435_SMRY (1).csv" \
    "Conut bakery Scaled Data/rep_s_00435_SMRY.csv"

echo "[$(date '+%H:%M:%S')] ============================================================"
echo "[$(date '+%H:%M:%S')]  All done!  Fully pushed to: $REMOTE_URL"
echo "[$(date '+%H:%M:%S')] ============================================================"
