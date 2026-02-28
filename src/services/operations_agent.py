"""Unified operations service layer — answers all 5 business objectives.

Loads data once at startup, caches cleaned datasets, exposes callable functions
that return deterministic JSON for each objective.
"""

from src.data.ingest_reports import ingest_all
from src.data.clean_reports import clean_all
from src.data.validate import validate_all
from src.models.combo_optimizer import run_combo_optimization
from src.models.demand_forecaster import run_demand_forecast
from src.models.expansion_feasibility import run_expansion_feasibility
from src.models.staffing_estimator import run_staffing_estimation
from src.models.growth_strategy import run_growth_strategy
from src.utils.logging import get_logger

log = get_logger(__name__)


class OperationsAgent:
    """Stateful service that loads data once and answers business queries."""

    def __init__(self):
        self._datasets = None

    def _ensure_loaded(self):
        if self._datasets is None:
            log.info("Loading and cleaning all datasets...")
            raw = ingest_all()
            self._datasets = clean_all(raw)
            warnings = validate_all(self._datasets)
            for key, msgs in warnings.items():
                for msg in msgs:
                    log.info(msg)
            log.info("All datasets loaded and validated.")

    def combo(self, min_support: float = 0.01, min_lift: float = 1.0, top_n: int = 10) -> dict:
        self._ensure_loaded()
        result = run_combo_optimization(
            self._datasets["sales_detail"],
            min_support=min_support,
            min_lift=min_lift,
            top_n=top_n,
        )
        return {"objective": "combo_optimization", **result}

    def demand(self, branch: str = "all", horizon_months: int = 3) -> dict:
        self._ensure_loaded()
        result = run_demand_forecast(
            self._datasets["monthly_sales"],
            branch=branch,
            horizon_months=horizon_months,
        )
        return {"objective": "demand_forecasting", **result}

    def expansion(self, risk_tolerance: str = "moderate") -> dict:
        self._ensure_loaded()
        result = run_expansion_feasibility(
            self._datasets["monthly_sales"],
            self._datasets["tax_summary"],
            self._datasets["customer_orders"],
            self._datasets["avg_menu_sales"],
            risk_tolerance=risk_tolerance,
        )
        return {"objective": "expansion_feasibility", **result}

    def staffing(self, branch: str = "all", period: str = "next_month") -> dict:
        self._ensure_loaded()
        result = run_staffing_estimation(
            self._datasets["attendance"],
            self._datasets["monthly_sales"],
            branch=branch,
            period=period,
        )
        return {"objective": "staffing_estimation", **result}

    def growth(self, category: str = "all") -> dict:
        self._ensure_loaded()
        result = run_growth_strategy(
            self._datasets["item_sales"],
            self._datasets["sales_detail"],
            self._datasets["customer_orders"],
            category=category,
        )
        return {"objective": "growth_strategy", **result}


# Singleton for the API to use
agent = OperationsAgent()
