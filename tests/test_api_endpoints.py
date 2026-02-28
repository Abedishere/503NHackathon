"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_combo_endpoint(client):
    resp = client.post("/combo", json={"min_support": 0.02, "min_lift": 0.5, "top_n": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective"] == "combo_optimization"


def test_demand_endpoint(client):
    resp = client.post("/demand", json={"branch": "all", "horizon_months": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective"] == "demand_forecasting"


def test_expansion_endpoint(client):
    resp = client.post("/expansion", json={"risk_tolerance": "moderate"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective"] == "expansion_feasibility"


def test_staffing_endpoint(client):
    resp = client.post("/staffing", json={"branch": "all", "period": "next_month"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective"] == "staffing_estimation"


def test_growth_endpoint(client):
    resp = client.post("/growth", json={"category": "all"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective"] == "growth_strategy"
