"""Demand forecasting per branch using exponential smoothing."""

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.features.demand_features import build_branch_timeseries
from src.features.time_series_utils import trend_label
from src.utils.logging import get_logger

log = get_logger(__name__)


def _clamp_forecast_entry(entry: dict) -> dict:
    """Clamp predicted, lower, and upper to be non-negative."""
    entry["predicted"] = max(0.0, entry["predicted"])
    entry["lower"] = max(0.0, entry["lower"])
    entry["upper"] = max(0.0, entry["upper"])
    return entry


def run_demand_forecast(
    monthly_sales: pd.DataFrame,
    branch: str = "all",
    horizon_months: int = 3,
) -> dict:
    """Forecast demand per branch using exponential smoothing.

    Returns dict with keys: scores, rationale, confidence, actions, data.
    Partial trailing months are excluded before fitting so the model does
    not extrapolate anomalous end-of-export drops into negative predictions.
    All forecast values are clamped >= 0 as a defensive layer.
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
    n = 0
    for branch_name, ts in timeseries.items():
        values = ts["total"].values
        dates = ts["date"].values
        n = len(values)

        if n < 3:
            # Too few points -- use simple average
            pred = float(np.mean(values)) if n > 0 else 0.0
            std = float(np.std(values)) if n > 1 else pred * 0.2
            forecast = []
            last_date = pd.Timestamp(dates[-1]) if n > 0 else pd.Timestamp.now()
            for i in range(1, horizon_months + 1):
                fdate = last_date + pd.DateOffset(months=i)
                forecast.append(_clamp_forecast_entry({
                    "month": fdate.strftime("%Y-%m"),
                    "predicted": round(pred, 2),
                    "lower": round(max(0.0, pred - 1.96 * std), 2),
                    "upper": round(pred + 1.96 * std, 2),
                }))
            tr = "insufficient_data"
        else:
            try:
                model = ExponentialSmoothing(
                    values,
                    trend="add",
                    seasonal=None,
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
                    forecast.append(_clamp_forecast_entry({
                        "month": fdate.strftime("%Y-%m"),
                        "predicted": round(float(pred_val), 2),
                        "lower": round(float(pred_val - 1.96 * std), 2),
                        "upper": round(float(pred_val + 1.96 * std), 2),
                    }))

                # Trend computed on the same partial-period-excluded series
                tr = trend_label(values)
            except Exception as e:
                log.warning(f"Forecasting failed for {branch_name}: {e}")
                pred = float(np.mean(values))
                std = float(np.std(values))
                forecast = []
                last_date = pd.Timestamp(dates[-1])
                for i in range(1, horizon_months + 1):
                    fdate = last_date + pd.DateOffset(months=i)
                    forecast.append(_clamp_forecast_entry({
                        "month": fdate.strftime("%Y-%m"),
                        "predicted": round(pred, 2),
                        "lower": round(max(0.0, pred - 1.96 * std), 2),
                        "upper": round(pred + 1.96 * std, 2),
                    }))
                tr = "fallback_average"

        scores.append({
            "branch": branch_name,
            "forecast": forecast,
            "trend": tr,
        })

    actions = []
    for s in scores:
        if s["trend"] == "increasing":
            actions.append(f"Increase inventory at {s['branch']} -- demand trending up.")
        elif s["trend"] == "decreasing":
            actions.append(f"Review {s['branch']} -- demand trending down, optimize costs.")

    return {
        "scores": scores,
        "rationale": f"Exponential smoothing on {n}-month branch sales history (partial months excluded).",
        "confidence": min(0.75, 0.4 + 0.07 * n),
        "actions": actions,
        "data": {"model": "exponential_smoothing", "training_months": n},
    }
