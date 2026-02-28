"""Pydantic request/response schemas for the Conut Operations API."""

from pydantic import BaseModel, Field
from typing import Any, List, Optional


# ---------- Request schemas ----------

class ComboRequest(BaseModel):
    min_support: float = Field(0.01, ge=0.001, le=1.0)
    min_lift: float = Field(1.0, ge=0.0)
    top_n: int = Field(10, ge=1, le=100)


class DemandRequest(BaseModel):
    branch: str = "all"
    horizon_months: int = Field(3, ge=1, le=12)


class ExpansionRequest(BaseModel):
    risk_tolerance: str = Field("moderate", pattern="^(conservative|moderate|aggressive)$")


class StaffingRequest(BaseModel):
    branch: str = "all"
    period: str = Field("next_month", pattern="^(next_month|next_quarter)$")


class GrowthRequest(BaseModel):
    category: str = Field("all", pattern="^(all|coffee|milkshake)$")


# ---------- Response schema ----------

class OperationsResponse(BaseModel):
    objective: str
    scores: List[Any]
    rationale: str
    confidence: float
    actions: List[str]
    data: Optional[dict] = None
