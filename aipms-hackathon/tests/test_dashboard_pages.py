from dashboard.pages import alert_feed, equipment_detail, fleet_overview, kpi_dashboard, maintenance_schedule


def test_page_modules_expose_show():
    for module in [fleet_overview, equipment_detail, maintenance_schedule, alert_feed, kpi_dashboard]:
        assert hasattr(module, "show")


def test_schedule_normalizer_accepts_dashboard_contract():
    df = maintenance_schedule.normalize_schedule_dataframe(
        [
            {
                "id": 1,
                "equipment_id": "EXC-01",
                "priority_tier": "critical",
                "priority_score": 0.85,
                "recommended_action": "Inspect hydraulic pump seals",
                "estimated_duration_hours": 4.0,
                "scheduled_window_start": "2026-04-18T08:00:00",
                "scheduled_window_end": "2026-04-18T12:00:00",
                "status": "scheduled",
                "estimated_cost": 220000.0,
            }
        ]
    )

    assert {"job_id", "equipment", "priority", "start_time", "end_time", "status"}.issubset(df.columns)


def test_alert_normalizer_accepts_dashboard_contract():
    df = alert_feed.normalize_alerts_dataframe(
        [
            {
                "id": 1,
                "equipment_id": "EXC-01",
                "severity": "critical",
                "message": "Hydraulic pump cavitation risk detected.",
                "triggered_at": "2026-04-18T08:00:00",
                "acknowledged": False,
            }
        ]
    )

    assert {"alert_id", "timestamp", "equipment", "type", "description", "acknowledged"}.issubset(df.columns)
