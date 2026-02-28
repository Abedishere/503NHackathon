"""Expansion feasibility analysis using branch health scoring."""

import numpy as np
import pandas as pd
from src.features.expansion_features import build_branch_health_scores
from src.utils.logging import get_logger

log = get_logger(__name__)

RISK_THRESHOLDS = {
    "conservative": 0.75,
    "moderate": 0.60,
    "aggressive": 0.45,
}


def run_expansion_feasibility(
    monthly_sales: pd.DataFrame,
    tax_summary: pd.DataFrame,
    customer_orders: pd.DataFrame,
    avg_menu_sales: pd.DataFrame,
    risk_tolerance: str = "moderate",
) -> dict:
    """Evaluate expansion feasibility based on branch health metrics.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    """
    health = build_branch_health_scores(
        monthly_sales, tax_summary, customer_orders, avg_menu_sales
    )

    if health.empty:
        return {
            "scores": [],
            "rationale": "No branch data available for expansion analysis.",
            "confidence": 0.0,
            "actions": [],
            "data": {},
        }

    # Normalize metrics to 0-1 scale for scoring
    metrics = ["total_revenue", "revenue_slope", "num_customers", "repeat_rate", "avg_order_value", "tax_contribution"]
    for col in metrics:
        if col in health.columns:
            max_val = health[col].max()
            if max_val > 0:
                health[f"{col}_norm"] = health[col] / max_val
            else:
                health[f"{col}_norm"] = 0.0

    # Composite feasibility score (weighted)
    weights = {
        "total_revenue_norm": 0.25,
        "revenue_slope_norm": 0.20,
        "num_customers_norm": 0.15,
        "repeat_rate_norm": 0.15,
        "avg_order_value_norm": 0.10,
        "tax_contribution_norm": 0.15,
    }

    health["feasibility_score"] = sum(
        health.get(col, 0) * w for col, w in weights.items()
    )

    # Determine risk level per branch
    threshold = RISK_THRESHOLDS.get(risk_tolerance, 0.60)

    scores = []
    for _, row in health.iterrows():
        score = float(row["feasibility_score"])
        if score >= 0.75:
            risk_level = "low"
            roi = "positive"
        elif score >= 0.50:
            risk_level = "moderate"
            roi = "uncertain"
        else:
            risk_level = "high"
            roi = "negative"

        scores.append({
            "branch": row["branch"],
            "feasibility_score": round(score, 3),
            "risk_level": risk_level,
            "roi_estimate": roi,
            "revenue_trend": row.get("revenue_trend", "unknown"),
            "repeat_rate": round(float(row.get("repeat_rate", 0)), 3),
            "months_active": int(row.get("months_active", 0)),
        })

    scores.sort(key=lambda x: x["feasibility_score"], reverse=True)

    # Expansion recommendation
    top_branch = scores[0] if scores else None
    actions = []
    if top_branch and top_branch["feasibility_score"] >= threshold:
        actions.append(
            f"Expansion is feasible. {top_branch['branch']} model shows strongest performance "
            f"(score={top_branch['feasibility_score']:.2f}). Replicate its operational model in a new location."
        )
        actions.append("Conduct foot-traffic and demographic study for candidate areas near existing high-demand zones.")
    else:
        actions.append("Expansion is not recommended at current risk tolerance. Focus on optimizing existing branches.")

    # Identify under-served demand signals
    growing = [s for s in scores if s["revenue_trend"] == "increasing"]
    if growing:
        actions.append(
            f"Branches with growing demand ({', '.join(s['branch'] for s in growing)}) suggest nearby expansion potential."
        )

    return {
        "scores": scores,
        "rationale": "Branch health scoring using revenue trends, customer metrics, and tax contributions.",
        "confidence": min(0.70, 0.4 + 0.08 * len(scores)),
        "actions": actions,
        "data": {
            "branches_analyzed": len(scores),
            "risk_tolerance": risk_tolerance,
            "metrics_used": ["revenue_trend", "customer_frequency", "repeat_rate", "tax_contribution"],
        },
    }
