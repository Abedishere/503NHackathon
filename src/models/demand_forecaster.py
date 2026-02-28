"""Demand forecasting per branch using exponential smoothing."""

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.features.demand_features import build_branch_timeseries
from src.utils.logging import get_logger

log = get_logger(__name__)


def run_demand_forecast(
    monthly_sales: pd.DataFrame,
    branch: str = "all",
    horizon_months: int = 3,
) -> dict:
    """Forecast demand per branch using exponential smoothing.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    """
    timeseries = build_branch_timeseries(monthly_sales)

    if branch != "all" and branch in timeseries:
        timeseries = {branch: timeseries[branch]}
    elif branch != "all":
        return {
            "scores": [],
            "rationale": f"Branch '{branch}' not found.",
            "confidence": 0.0,
            "actions": [],
            "data": {"available_branches": list(timeseries.keys())},
        }

    scores = []
    for branch_name, ts in timeseries.items():
        values = ts["total"].values
        dates = ts["date"].values
        n = len(values)

        if n < 3:
            # Too few points — use simple average
            pred = float(np.mean(values))
            std = float(np.std(values)) if n > 1 else pred * 0.2
            forecast = []
            last_date = pd.Timestamp(dates[-1])
            for i in range(1, horizon_months + 1):
                fdate = last_date + pd.DateOffset(months=i)
                forecast.append({
                    "month": fdate.strftime("%Y-%m"),
                    "predicted": round(pred, 2),
                    "lower": round(pred - 1.96 * std, 2),
                    "upper": round(pred + 1.96 * std, 2),
                })
            trend = "insufficient_data"
        else:
            try:
                model = ExponentialSmoothing(
                    values,
                    trend="add",
                    seasonal=None,  # Only 5 months of data — no seasonal component
                    initialization_method="estimated",
                )
                fitted = model.fit(optimized=True)
                pred_values = fitted.forecast(horizon_months)
                residuals = fitted.resid
                std = float(np.std(residuals))

                forecast = []
                last_date = pd.Timestamp(dates[-1])
                for i, pred_val in enumerate(pred_values):
                    fdate = last_date + pd.DateOffset(months=i + 1)
                    forecast.append({
                        "month": fdate.strftime("%Y-%m"),
                        "predicted": round(float(pred_val), 2),
                        "lower": round(float(pred_val - 1.96 * std), 2),
                        "upper": round(float(pred_val + 1.96 * std), 2),
                    })

                slope = np.polyfit(np.arange(n), values, 1)[0]
                trend = "increasing" if slope > 0 else "decreasing"
            except Exception as e:
                log.warning(f"Forecasting failed for {branch_name}: {e}")
                pred = float(np.mean(values))
                std = float(np.std(values))
                forecast = []
                last_date = pd.Timestamp(dates[-1])
                for i in range(1, horizon_months + 1):
                    fdate = last_date + pd.DateOffset(months=i)
                    forecast.append({
                        "month": fdate.strftime("%Y-%m"),
                        "predicted": round(pred, 2),
                        "lower": round(pred - 1.96 * std, 2),
                        "upper": round(pred + 1.96 * std, 2),
                    })
                trend = "fallback_average"

        scores.append({
            "branch": branch_name,
            "forecast": forecast,
            "trend": trend,
        })

    actions = []
    for s in scores:
        if s["trend"] == "increasing":
            actions.append(f"Increase inventory at {s['branch']} — demand trending up.")
        elif s["trend"] == "decreasing":
            actions.append(f"Review {s['branch']} — demand trending down, optimize costs.")

    return {
        "scores": scores,
        "rationale": f"Exponential smoothing on {n}-month branch sales history.",
        "confidence": min(0.75, 0.4 + 0.07 * n),
        "actions": actions,
        "data": {"model": "exponential_smoothing", "training_months": n},
    }
