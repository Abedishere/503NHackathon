"""Shared time-series utilities for demand forecasting and expansion features.

Primary role: detect and exclude anomalous trailing partial periods (e.g. a
partially-exported final month) before trend/slope computation.  The clamping
in model output is a separate defensive layer; this utility is the primary fix.
"""

import numpy as np
import pandas as pd


def detect_partial_period_cutoff(values: np.ndarray, threshold: float = 0.30) -> int:
    """Return the index to slice values up to, excluding anomalous trailing months.

    A trailing month is considered partial/anomalous if its value is less than
    `threshold` * mean(prior_months).  We exclude all such trailing months so
    that trend/slope is computed on complete-period data only.

    Returns the number of values to keep (i.e., values[:n] gives the clean series).
    If all months look normal, returns len(values).

    Args:
        values: Array of monthly sales values, ordered oldest first.
        threshold: Fraction of the prior-months mean below which a month is
                   considered anomalous.  Default 0.30 (30%).
    """
    n = len(values)
    if n < 2:
        return n

    # Work backwards from the end
    cutoff = n
    for i in range(n - 1, 0, -1):
        prior_mean = np.mean(values[:i])
        if prior_mean > 0 and values[i] < threshold * prior_mean:
            cutoff = i
        else:
            break  # Stop as soon as a non-anomalous month is found

    return max(cutoff, 2)  # Always keep at least 2 points


def clean_series_for_trend(values: np.ndarray, threshold: float = 0.30) -> np.ndarray:
    """Return values with anomalous trailing partial months removed."""
    cutoff = detect_partial_period_cutoff(values, threshold)
    return values[:cutoff]


def compute_slope(values: np.ndarray) -> float:
    """Fit a linear slope over `values` using index positions [0, 1, 2, ...]."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, values, 1)[0])


def trend_label(values: np.ndarray, threshold: float = 0.30) -> str:
    """Return 'increasing' or 'decreasing' after excluding partial trailing months."""
    clean = clean_series_for_trend(values, threshold)
    slope = compute_slope(clean)
    return "increasing" if slope > 0 else "decreasing"
