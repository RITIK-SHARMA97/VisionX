import importlib

from dashboard import api_client


def test_fleet_overview_fallback_returns_blueprint_equipment(monkeypatch):
    monkeypatch.setattr(api_client, "api_call", lambda *args, **kwargs: None)

    fleet = api_client.get_fleet_overview()

    assert [item["id"] for item in fleet[:3]] == ["EXC-01", "DMP-03", "CVR-01"]
    assert {"id", "name", "type", "status", "failure_prob", "rul_hours", "anomaly_score"}.issubset(
        fleet[0].keys()
    )


def test_alerts_fallback_returns_dashboard_contract(monkeypatch):
    monkeypatch.setattr(api_client, "api_call", lambda *args, **kwargs: None)

    alerts = api_client.get_alerts()

    assert alerts
    assert {"id", "equipment_id", "severity", "message", "acknowledged"}.issubset(alerts[0].keys())


def test_schedule_fallback_returns_dashboard_contract(monkeypatch):
    monkeypatch.setattr(api_client, "api_call", lambda *args, **kwargs: None)

    schedule = api_client.get_maintenance_schedule()

    assert schedule
    assert {
        "equipment_id",
        "priority_tier",
        "priority_score",
        "recommended_action",
        "estimated_duration_hours",
    }.issubset(schedule[0].keys())


def test_dashboard_kpi_fallback_returns_summary(monkeypatch):
    monkeypatch.setattr(api_client, "api_call", lambda *args, **kwargs: None)

    kpi = api_client.get_dashboard_kpi()

    assert kpi is not None
    assert {"total_equipment", "critical_count", "warning_count", "normal_count"}.issubset(kpi.keys())


def test_kpi_dashboard_page_exists():
    module = importlib.import_module("dashboard.pages.kpi_dashboard")

    assert hasattr(module, "show")
