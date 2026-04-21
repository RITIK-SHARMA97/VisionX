import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_health_endpoint_exposes_phase6_status_contract():
    from api.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "ok"
    assert "services" in data
    assert "models" in data


def test_equipment_endpoint_returns_phase6_fleet_contract():
    from api.main import app

    client = TestClient(app)
    response = client.get("/equipment")

    assert response.status_code == 200
    fleet = response.json()
    assert len(fleet) >= 3
    assert {"id", "name", "type", "status", "failure_prob", "rul_hours", "anomaly_score"}.issubset(
        fleet[0].keys()
    )


def test_alert_acknowledgement_endpoint_returns_audit_fields():
    from api.main import app

    client = TestClient(app)
    response = client.post("/alerts/1/acknowledge", json={"acknowledged_by": "phase6-tester"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "acknowledged"
    assert payload["alert_id"] == 1
    assert payload["acknowledged_by"] == "phase6-tester"
    assert payload["acknowledged_at"]


def test_demo_script_runs_under_cp1252_without_unicode_crash():
    demo_script = PROJECT_ROOT / "demo_13_steps.py"
    command = [
        sys.executable,
        "-X",
        "utf8=0",
        str(demo_script),
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env={"PYTHONIOENCODING": "cp1252"},
        capture_output=True,
        text=True,
        timeout=30,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "UnicodeEncodeError" not in combined_output
