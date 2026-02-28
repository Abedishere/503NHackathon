"""FastAPI REST API for the Conut Operations Agent."""

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from src.api.schemas import (
    ComboRequest,
    DemandRequest,
    ExpansionRequest,
    StaffingRequest,
    GrowthRequest,
    OperationsResponse,
    EDATableResponse,
)
from src.services.operations_agent import agent
from src.config import EDA_TABLES_DIR

app = FastAPI(
    title="Conut Operations Agent API",
    description="AI-Driven Chief of Operations Agent for Conut bakery",
    version="1.0.0",
)


def _load_eda_csv(filename: str, branch: str = "all") -> tuple[list, str]:
    """Load an EDA output CSV, optionally filtering by branch. Returns (rows, effective_branch)."""
    path = EDA_TABLES_DIR / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{filename} not found. Run: python -m eda.scripts.run_eda",
        )
    df = pd.read_csv(path)
    if branch != "all" and "branch" in df.columns:
        df = df[df["branch"] == branch]
    return df.to_dict("records"), branch


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/combo", response_model=OperationsResponse)
def combo(req: ComboRequest):
    return agent.combo(
        min_support=req.min_support,
        min_lift=req.min_lift,
        top_n=req.top_n,
    )


@app.post("/demand", response_model=OperationsResponse)
def demand(req: DemandRequest):
    return agent.demand(branch=req.branch, horizon_months=req.horizon_months)


@app.post("/expansion", response_model=OperationsResponse)
def expansion(req: ExpansionRequest):
    return agent.expansion(risk_tolerance=req.risk_tolerance)


@app.post("/staffing", response_model=OperationsResponse)
def staffing(req: StaffingRequest):
    return agent.staffing(branch=req.branch, period=req.period)


@app.post("/growth", response_model=OperationsResponse)
def growth(req: GrowthRequest):
    return agent.growth(category=req.category)


# ---------------------------------------------------------------------------
# EDA data endpoints — serve pre-computed tables from eda/outputs/tables/
# ---------------------------------------------------------------------------

@app.get("/eda/branch-kpis", response_model=EDATableResponse)
def eda_branch_kpis(branch: str = Query("all", description="Branch name or 'all'")):
    rows, b = _load_eda_csv("branch_kpis.csv", branch)
    return EDATableResponse(table="branch_kpis", branch=b, rows=rows, count=len(rows))


@app.get("/eda/combos", response_model=EDATableResponse)
def eda_combos(
    branch: str = Query("all", description="Branch name or 'all'"),
    top_n: int = Query(25, ge=1, le=200),
):
    rows, b = _load_eda_csv("combo_pairs_scored_all_branches.csv", branch)
    return EDATableResponse(table="combo_pairs_scored", branch=b, rows=rows[:top_n], count=len(rows))


@app.get("/eda/growth", response_model=EDATableResponse)
def eda_growth(branch: str = Query("all", description="Branch name or 'all'")):
    rows, b = _load_eda_csv("growth_metrics_all_branches.csv", branch)
    return EDATableResponse(table="growth_metrics", branch=b, rows=rows, count=len(rows))


@app.get("/eda/channels", response_model=EDATableResponse)
def eda_channels(branch: str = Query("all", description="Branch name or 'all'")):
    rows, b = _load_eda_csv("channel_shares.csv", branch)
    return EDATableResponse(table="channel_shares", branch=b, rows=rows, count=len(rows))


@app.get("/eda/staffing", response_model=EDATableResponse)
def eda_staffing(branch: str = Query("all", description="Branch name or 'all'")):
    rows, b = _load_eda_csv("attendance_daily_hours.csv", branch)
    return EDATableResponse(table="attendance_daily_hours", branch=b, rows=rows, count=len(rows))


@app.get("/eda/customers", response_model=EDATableResponse)
def eda_customers(branch: str = Query("all", description="Branch name or 'all'")):
    rows, b = _load_eda_csv("customer_rfm_lite.csv", branch)
    return EDATableResponse(table="customer_rfm_lite", branch=b, rows=rows, count=len(rows))
