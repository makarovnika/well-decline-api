import math

import pytest
from fastapi.testclient import TestClient

import decline
from app_final import WELLS, app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_list_wells_filtered_by_field():
    response = client.get("/wells", params={"field": "южное"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["wells"][0]["name"] == "W-201"


def test_unknown_well_returns_404():
    response = client.get("/wells/999")
    assert response.status_code == 404


def test_forecast_rate_declines_month_by_month():
    response = client.get("/wells/1/forecast", params={"months": 24})
    assert response.status_code == 200
    rates = [p["rate_m3_per_day"] for p in response.json()["forecast"]]
    assert len(rates) == 25
    assert rates[0] == 120
    assert all(later < earlier for earlier, later in zip(rates, rates[1:]))


def test_eur_reaches_economic_limit():
    response = client.get("/wells/2/eur", params={"q_limit": 10})
    assert response.status_code == 200
    body = response.json()
    # Экспоненциальное падение: t = ln(qi / q_limit) / di
    assert body["months_to_limit"] == pytest.approx(math.log(85 / 10) / 0.09, abs=0.1)
    assert body["eur_m3"] > 0


def test_invalid_decline_parameter_is_rejected():
    response = client.get("/decline/rate", params={"qi": 100, "di": 0.1, "b": 1.5, "t": 12})
    assert response.status_code == 422


def test_create_well():
    payload = {"name": "W-300", "field": "Западное", "qi": 60, "di": 0.07, "b": 0.3}
    response = client.post("/wells", json=payload)
    assert response.status_code == 201
    well_id = response.json()["id"]
    assert client.get(f"/wells/{well_id}").json()["name"] == "W-300"
    del WELLS[well_id]


@pytest.mark.parametrize("b", [0, 0.5, 1])
def test_cumulative_matches_numeric_integral(b):
    qi, di, t = 100, 0.08, 36
    steps = 20000
    h = t / steps
    numeric = sum(decline.rate(qi, di, b, (i + 0.5) * h) for i in range(steps)) * h
    numeric *= decline.DAYS_PER_MONTH
    assert decline.cumulative(qi, di, b, t) == pytest.approx(numeric, rel=1e-6)
