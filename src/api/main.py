"""FastAPI REST API for the Conut Operations Agent."""

from fastapi import FastAPI
from src.api.schemas import (
    ComboRequest,
    DemandRequest,
    ExpansionRequest,
    StaffingRequest,
    GrowthRequest,
    OperationsResponse,
)
from src.services.operations_agent import agent

app = FastAPI(
    title="Conut Operations Agent API",
    description="AI-Driven Chief of Operations Agent for Conut bakery",
    version="1.0.0",
)


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
