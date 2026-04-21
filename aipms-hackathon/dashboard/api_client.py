"""
AIPMS dashboard data client.

This module presents one stable dashboard contract regardless of whether the
data comes from the hackathon API, the local SQLite database, or demo defaults.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 5.0
RETRY_COUNT = 2
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "aipms.db"

EQUIPMENT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "EXC-01": {
        "id": "EXC-01",
        "name": "Rope Shovel #1 - North Bench",
        "type": "excavator",
        "location": "North Bench",
        "status": "critical",
        "failure_prob": 0.78,
        "rul_hours": 31.5,
        "anomaly_score": 0.82,
        "efficiency_percent": 81.5,
        "operating_temperature_c": 96.4,
        "operating_pressure_bar": 5.8,
        "vibration_mm_s": 7.6,
        "rpm": 1835,
        "total_operating_hours": 12480.0,
        "failure_mode_hint": "FM-06 Hydraulic pump cavitation / seal wear",
        "recommended_action": "Inspect hydraulic pump seals and verify flow rate within 24 hours.",
        "estimated_duration_hours": 4.0,
        "estimated_cost": 220000.0,
        "top_features": [
            {"sensor": "Hydraulic Pressure", "shap": 0.42, "pct": 42},
            {"sensor": "Fluid Temperature", "shap": 0.35, "pct": 35},
            {"sensor": "Pump Flow Rate", "shap": 0.23, "pct": 23},
        ],
    },
    "DMP-03": {
        "id": "DMP-03",
        "name": "Dumper Truck #3 - Haul Road",
        "type": "dumper",
        "location": "Haul Road",
        "status": "warning",
        "failure_prob": 0.54,
        "rul_hours": 89.0,
        "anomaly_score": 0.62,
        "efficiency_percent": 88.0,
        "operating_temperature_c": 79.2,
        "operating_pressure_bar": 4.3,
        "vibration_mm_s": 5.3,
        "rpm": 1640,
        "total_operating_hours": 9420.0,
        "failure_mode_hint": "FM-02 Turbocharger bearing degradation",
        "recommended_action": "Check turbocharger bearings during next planned service window.",
        "estimated_duration_hours": 3.5,
        "estimated_cost": 180000.0,
        "top_features": [
            {"sensor": "Boost Pressure", "shap": 0.39, "pct": 39},
            {"sensor": "Exhaust Temperature", "shap": 0.34, "pct": 34},
            {"sensor": "Fuel Consumption", "shap": 0.18, "pct": 18},
        ],
    },
    "CVR-01": {
        "id": "CVR-01",
        "name": "Conveyor Belt #1 - CHP Feed",
        "type": "conveyor",
        "location": "CHP Feed",
        "status": "normal",
        "failure_prob": 0.12,
        "rul_hours": 312.0,
        "anomaly_score": 0.15,
        "efficiency_percent": 94.0,
        "operating_temperature_c": 52.0,
        "operating_pressure_bar": 2.1,
        "vibration_mm_s": 2.8,
        "rpm": 920,
        "total_operating_hours": 15320.0,
        "failure_mode_hint": "No active failure mode",
        "recommended_action": "Continue normal monitoring.",
        "estimated_duration_hours": 2.0,
        "estimated_cost": 50000.0,
        "top_features": [
            {"sensor": "Motor Temperature", "shap": 0.12, "pct": 12},
            {"sensor": "Belt Tension", "shap": 0.10, "pct": 10},
            {"sensor": "Roller Vibration", "shap": 0.08, "pct": 8},
        ],
    },
}


def api_call(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = REQUEST_TIMEOUT,
) -> Optional[Dict[str, Any] | List[Any]]:
    """Make an HTTP request to the backend."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=timeout)
        else:
            logger.warning("Unsupported HTTP method: %s", method)
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Timeout calling %s", endpoint)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to %s%s", API_BASE_URL, endpoint)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error %s on %s", exc.response.status_code, endpoint)
    except Exception as exc:
        logger.error("API error calling %s: %s", endpoint, exc)
    return None


def _sqlite_query(query: str, params: tuple[Any, ...] = ()) -> List[sqlite3.Row]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    except sqlite3.Error as exc:
        logger.warning("SQLite query failed: %s", exc)
        return []
    finally:
        conn.close()


def _parse_timestamp(value: Any, fallback: Optional[datetime] = None) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
    return fallback or datetime.now()


def _status_rank(status: str) -> int:
    return {"critical": 3, "warning": 2, "normal": 1, "offline": 0}.get(status, 0)


def _coerce_float(value: Any, fallback: float) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _default_equipment(equipment_id: str) -> Dict[str, Any]:
    default = EQUIPMENT_DEFAULTS.get(equipment_id)
    if default:
        return {
            **default,
            "last_updated": datetime.now().isoformat(),
        }
    return {
        "id": equipment_id,
        "name": equipment_id,
        "type": "equipment",
        "location": "Production Area",
        "status": "normal",
        "failure_prob": 0.15,
        "rul_hours": 250.0,
        "anomaly_score": 0.18,
        "efficiency_percent": 90.0,
        "operating_temperature_c": 48.0,
        "operating_pressure_bar": 3.0,
        "vibration_mm_s": 2.2,
        "rpm": 1200,
        "total_operating_hours": 5000.0,
        "failure_mode_hint": "No active failure mode",
        "recommended_action": "Continue monitoring.",
        "estimated_duration_hours": 2.0,
        "estimated_cost": 60000.0,
        "top_features": [],
        "last_updated": datetime.now().isoformat(),
    }


def _local_predictions_by_equipment() -> Dict[str, sqlite3.Row]:
    rows = _sqlite_query(
        """
        SELECT p.*
        FROM predictions p
        INNER JOIN (
            SELECT equipment_id, MAX(timestamp) AS max_ts
            FROM predictions
            GROUP BY equipment_id
        ) latest
            ON p.equipment_id = latest.equipment_id
           AND p.timestamp = latest.max_ts
        """
    )
    return {row["equipment_id"]: row for row in rows}


def _local_equipment_rows() -> List[sqlite3.Row]:
    return _sqlite_query("SELECT * FROM equipment ORDER BY id")


def _normalize_fleet_item(item: Dict[str, Any]) -> Dict[str, Any]:
    equipment_id = item.get("id") or item.get("equipment_id") or "unknown"
    default = _default_equipment(equipment_id)
    status = str(item.get("status", default["status"])).lower()
    normalized = {
        **default,
        "id": equipment_id,
        "name": item.get("name", default["name"]),
        "type": item.get("type", default["type"]),
        "location": item.get("location", default["location"]),
        "status": status,
        "failure_prob": _coerce_float(item.get("failure_prob"), default["failure_prob"]),
        "rul_hours": _coerce_float(item.get("rul_hours"), default["rul_hours"]),
        "anomaly_score": _coerce_float(item.get("anomaly_score"), default["anomaly_score"]),
        "total_operating_hours": _coerce_float(
            item.get("total_operating_hours"),
            default["total_operating_hours"],
        ),
        "last_updated": item.get("last_updated", default["last_updated"]),
        "top_features": item.get("top_features", default["top_features"]),
        "failure_mode_hint": item.get("failure_mode_hint", default["failure_mode_hint"]),
        "recommended_action": item.get("recommended_action", default["recommended_action"]),
        "estimated_duration_hours": _coerce_float(
            item.get("estimated_duration_hours"),
            default["estimated_duration_hours"],
        ),
        "estimated_cost": _coerce_float(item.get("estimated_cost"), default["estimated_cost"]),
    }
    return normalized


def _fleet_from_db() -> List[Dict[str, Any]]:
    prediction_rows = _local_predictions_by_equipment()
    fleet: List[Dict[str, Any]] = []
    equipment_rows = _local_equipment_rows()

    if not equipment_rows:
        return get_sample_fleet_overview()

    for row in equipment_rows:
        default = _default_equipment(row["id"])
        item = {
            **default,
            "id": row["id"],
            "name": row["name"] or default["name"],
            "type": row["type"] or default["type"],
            "location": row["location"] or default["location"],
            "total_operating_hours": row["total_operating_hours"] or default["total_operating_hours"],
            "last_updated": row["last_updated"] or default["last_updated"],
        }
        latest_prediction = prediction_rows.get(row["id"])
        if latest_prediction is not None:
            item.update({
                "anomaly_score": latest_prediction["anomaly_score"],
                "failure_prob": latest_prediction["failure_prob"],
                "rul_hours": latest_prediction["rul_hours"],
                "status": latest_prediction["anomaly_label"],
                "top_features": latest_prediction["top_features_json"] or [],
            })
        fleet.append(_normalize_fleet_item(item))

    fleet.sort(key=lambda equipment: (-_status_rank(equipment["status"]), equipment["id"]))
    return fleet


def _sample_sensor_rows(equipment_id: str, limit: int) -> List[Dict[str, Any]]:
    default = _default_equipment(equipment_id)
    now = datetime.now()
    rows: List[Dict[str, Any]] = []
    history_points = min(limit, 24)
    for hours_ago in range(history_points, 0, -1):
        ts = (now - timedelta(hours=hours_ago)).isoformat()
        rows.extend(
            [
                {
                    "timestamp": ts,
                    "sensor_name": "temperature",
                    "value": round(default["operating_temperature_c"] - hours_ago * 0.2, 2),
                    "unit": "degC",
                    "data_quality_flag": "ok",
                },
                {
                    "timestamp": ts,
                    "sensor_name": "pressure",
                    "value": round(default["operating_pressure_bar"] + hours_ago * 0.03, 2),
                    "unit": "bar",
                    "data_quality_flag": "ok",
                },
                {
                    "timestamp": ts,
                    "sensor_name": "vibration",
                    "value": round(default["vibration_mm_s"] - hours_ago * 0.04, 2),
                    "unit": "mm/s",
                    "data_quality_flag": "ok",
                },
                {
                    "timestamp": ts,
                    "sensor_name": "rpm",
                    "value": round(default["rpm"] + hours_ago * 2, 2),
                    "unit": "rpm",
                    "data_quality_flag": "ok",
                },
            ]
        )
    return rows[-limit:]


def _sample_prediction_history(equipment_id: str, days: int = 30) -> List[Dict[str, Any]]:
    default = _default_equipment(equipment_id)
    now = datetime.now()
    history: List[Dict[str, Any]] = []
    start_rul = default["rul_hours"] + (days * 8)
    for day in range(days, 0, -1):
        timestamp = (now - timedelta(days=day)).isoformat()
        failure_prob = max(0.05, min(0.95, default["failure_prob"] - day * 0.01))
        anomaly_score = max(0.05, min(0.95, default["anomaly_score"] - day * 0.012))
        rul_hours = max(6.0, start_rul - (days - day) * 8)
        history.append(
            {
                "timestamp": timestamp,
                "anomaly_score": round(anomaly_score, 3),
                "anomaly_label": _status_from_scores(failure_prob, anomaly_score, rul_hours),
                "failure_prob": round(failure_prob, 3),
                "rul_hours": round(rul_hours, 1),
                "rul_confidence_low": round(max(0.0, rul_hours - 18), 1),
                "rul_confidence_high": round(rul_hours + 24, 1),
                "top_features_json": default["top_features"],
            }
        )
    history.append(
        {
            "timestamp": now.isoformat(),
            "anomaly_score": default["anomaly_score"],
            "anomaly_label": default["status"],
            "failure_prob": default["failure_prob"],
            "rul_hours": default["rul_hours"],
            "rul_confidence_low": max(0.0, round(default["rul_hours"] - 18, 1)),
            "rul_confidence_high": round(default["rul_hours"] + 24, 1),
            "top_features_json": default["top_features"],
        }
    )
    return history


def _status_from_scores(failure_prob: float, anomaly_score: float, rul_hours: float) -> str:
    if failure_prob >= 0.70 or anomaly_score >= 0.70 or rul_hours <= 48:
        return "critical"
    if failure_prob >= 0.50 or anomaly_score >= 0.40 or rul_hours <= 168:
        return "warning"
    return "normal"


def get_fleet_overview() -> List[Dict[str, Any]]:
    """Fetch all equipment with current status."""
    data = api_call("/equipment")
    if isinstance(data, list) and data:
        return [_normalize_fleet_item(item) for item in data]
    return _fleet_from_db()


def get_equipment_detail(equipment_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed info for a single equipment unit."""
    data = api_call(f"/equipment/{equipment_id}")
    if isinstance(data, dict) and data:
        fleet_item = _normalize_fleet_item(data)
    else:
        fleet_item = next(
            (item for item in get_fleet_overview() if item["id"] == equipment_id),
            _default_equipment(equipment_id),
        )

    latest_rul = get_equipment_rul(equipment_id) or {}
    fleet_item.update(
        {
            "current_rul_days": round(_coerce_float(latest_rul.get("rul_hours"), fleet_item["rul_hours"]) / 24),
            "uptime_hours": round(fleet_item["total_operating_hours"] * 0.68),
            "maintenance_due_days": max(0, round(_coerce_float(latest_rul.get("rul_hours"), fleet_item["rul_hours"]) / 24) - 1),
            "last_maintenance": (datetime.now() - timedelta(days=12)).isoformat(),
            "next_maintenance": (datetime.now() + timedelta(days=max(1, round(fleet_item["rul_hours"] / 24)))).isoformat(),
            "operating_temperature_c": fleet_item["operating_temperature_c"],
            "operating_pressure_bar": fleet_item["operating_pressure_bar"],
            "vibration_mm_s": fleet_item["vibration_mm_s"],
            "rpm": fleet_item["rpm"],
            "efficiency_percent": fleet_item["efficiency_percent"],
        }
    )
    return fleet_item


def get_equipment_sensors(equipment_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch sensor readings for equipment."""
    data = api_call(f"/equipment/{equipment_id}/sensors?limit={limit}")
    if isinstance(data, list) and data:
        return data

    rows = _sqlite_query(
        """
        SELECT timestamp, sensor_name, value, unit, data_quality_flag
        FROM sensor_readings
        WHERE equipment_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (equipment_id, limit),
    )
    if rows:
        return [dict(row) for row in reversed(rows)]
    return _sample_sensor_rows(equipment_id, limit)


def get_equipment_predictions(equipment_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Fetch prediction history for equipment."""
    data = api_call(f"/equipment/{equipment_id}/predictions?days={days}")
    if isinstance(data, list) and data:
        return data

    rows = _sqlite_query(
        """
        SELECT timestamp, anomaly_score, anomaly_label, failure_prob, rul_hours,
               rul_confidence_low, rul_confidence_high, top_features_json
        FROM predictions
        WHERE equipment_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (equipment_id, days),
    )
    if rows:
        return [dict(row) for row in reversed(rows)]
    return _sample_prediction_history(equipment_id, days=min(days, 30))


def get_equipment_rul(equipment_id: str) -> Optional[Dict[str, Any]]:
    """Fetch latest RUL with confidence interval."""
    data = api_call(f"/equipment/{equipment_id}/rul")
    if isinstance(data, dict) and data:
        return data

    history = get_equipment_predictions(equipment_id, days=30)
    if history:
        latest = history[-1]
        return {
            "rul_hours": latest["rul_hours"],
            "rul_cycles": round(latest["rul_hours"] * 3.6),
            "ci_low": latest.get("rul_confidence_low", max(0.0, latest["rul_hours"] - 18)),
            "ci_high": latest.get("rul_confidence_high", latest["rul_hours"] + 24),
            "staleness_flag": False,
        }
    return {
        "rul_hours": 250.0,
        "rul_cycles": 1200,
        "ci_low": 180.0,
        "ci_high": 350.0,
        "staleness_flag": False,
    }


def get_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    days: int = 7,
) -> List[Dict[str, Any]]:
    """Fetch alerts with optional filtering."""
    endpoint = "/alerts"
    params = []
    if severity:
        params.append(f"severity={severity}")
    if acknowledged is not None:
        params.append(f"acknowledged={str(acknowledged).lower()}")
    if days:
        params.append(f"days={days}")
    if params:
        endpoint += "?" + "&".join(params)

    data = api_call(endpoint)
    if isinstance(data, list) and data:
        return data

    rows = _sqlite_query(
        """
        SELECT id, equipment_id, triggered_at, severity, message, top_sensors,
               failure_mode_hint, acknowledged, acknowledged_at, acknowledged_by
        FROM alerts
        ORDER BY triggered_at DESC
        """
    )
    alerts = [dict(row) for row in rows]
    if not alerts:
        alerts = get_sample_alerts()

    filtered: List[Dict[str, Any]] = []
    cutoff = datetime.now() - timedelta(days=days)
    for alert in alerts:
        alert_time = _parse_timestamp(alert.get("triggered_at"), datetime.now())
        if severity and str(alert.get("severity", "")).lower() != severity.lower():
            continue
        if acknowledged is not None and bool(alert.get("acknowledged")) != acknowledged:
            continue
        if alert_time < cutoff:
            continue
        filtered.append(alert)
    return filtered


def acknowledge_alert(alert_id: int, user_id: str = "demo_user") -> Optional[Dict[str, Any]]:
    """Acknowledge an alert."""
    response = api_call(
        f"/alerts/{alert_id}/acknowledge",
        method="POST",
        json_data={"acknowledged_by": user_id},
    )
    if response:
        return response

    rows = _sqlite_query("SELECT id FROM alerts WHERE id = ?", (alert_id,))
    if rows:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                """
                UPDATE alerts
                SET acknowledged = 1,
                    acknowledged_by = ?,
                    acknowledged_at = ?
                WHERE id = ?
                """,
                (user_id, datetime.now().isoformat(), alert_id),
            )
            conn.commit()
        finally:
            conn.close()
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_by": user_id,
        "acknowledged_at": datetime.now().isoformat(),
    }


def get_maintenance_schedule(days: int = 7) -> List[Dict[str, Any]]:
    """Fetch maintenance schedule for specified days."""
    data = api_call(f"/schedule?days={days}")
    if isinstance(data, list) and data:
        return data

    rows = _sqlite_query(
        """
        SELECT id, equipment_id, created_at, priority_score, priority_tier, failure_prob,
               rul_hours, recommended_action, estimated_duration_hours,
               scheduled_window_start, scheduled_window_end, status
        FROM maintenance_jobs
        ORDER BY priority_score DESC, created_at ASC
        """
    )
    schedule = [dict(row) for row in rows]
    if schedule:
        return schedule
    return get_sample_schedule()


def get_dashboard_kpi() -> Optional[Dict[str, Any]]:
    """Fetch KPI summary for manager dashboard."""
    data = api_call("/dashboard/kpi")
    if isinstance(data, dict) and data:
        return data

    fleet = get_fleet_overview()
    alerts = get_alerts(days=7)
    schedule = get_maintenance_schedule(days=7)
    total_cost = sum(_coerce_float(job.get("estimated_cost"), 0.0) for job in schedule)
    return {
        "total_equipment": len(fleet),
        "critical_count": sum(1 for equipment in fleet if equipment["status"] == "critical"),
        "warning_count": sum(1 for equipment in fleet if equipment["status"] == "warning"),
        "normal_count": sum(1 for equipment in fleet if equipment["status"] == "normal"),
        "alerts_today": sum(
            1 for alert in alerts if _parse_timestamp(alert["triggered_at"]).date() == datetime.now().date()
        ),
        "estimated_cost_7day": total_cost,
        "average_failure_probability": round(
            sum(equipment["failure_prob"] for equipment in fleet) / len(fleet), 3
        ) if fleet else 0.0,
    }


def get_dashboard_summary() -> Optional[Dict[str, Any]]:
    """Fetch lightweight summary for rapid updates."""
    data = api_call("/dashboard/summary")
    if isinstance(data, dict) and data:
        return data
    kpi = get_dashboard_kpi() or {}
    return {
        "fleet": get_fleet_overview(),
        "kpi": kpi,
        "alerts": get_alerts(days=1),
        "generated_at": datetime.now().isoformat(),
    }


def get_api_health() -> Optional[Dict[str, Any]]:
    """Check API and backend health."""
    return api_call("/health")


def format_timestamp(iso_string: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = _parse_timestamp(iso_string)
        return dt.strftime("%H:%M:%S")
    except Exception as exc:
        logger.warning("Error formatting timestamp: %s", exc)
        return str(iso_string)


def status_badge(status: str) -> str:
    """Return badge text for equipment status."""
    badges = {
        "critical": "CRITICAL",
        "warning": "WARNING",
        "normal": "NORMAL",
        "offline": "OFFLINE",
    }
    return badges.get(str(status).lower(), "UNKNOWN")


def equipment_icon(equipment_type: str) -> str:
    """Return icon for equipment type."""
    icons = {
        "excavator": "EXC",
        "dumper": "DMP",
        "conveyor": "CVR",
        "drill": "DRL",
    }
    return icons.get(str(equipment_type).lower(), "EQP")


def severity_color(severity: str) -> str:
    """Return hex color for alert severity."""
    colors = {
        "critical": "#dc3545",
        "warning": "#ffc107",
        "normal": "#28a745",
    }
    return colors.get(str(severity).lower(), "#6c757d")


def get_alert_stats() -> Optional[Dict[str, Any]]:
    """Get alert statistics summary."""
    data = api_call("/alerts/stats")
    if isinstance(data, dict) and data:
        return data
    alerts = get_alerts(days=7)
    total_alerts = len(alerts)
    unack = sum(1 for alert in alerts if not alert.get("acknowledged"))
    critical = sum(1 for alert in alerts if str(alert.get("severity")).lower() == "critical")
    high = sum(1 for alert in alerts if str(alert.get("severity")).lower() in {"critical", "warning"})
    return {
        "total_alerts": total_alerts,
        "unacknowledged": unack,
        "critical": critical,
        "high": high,
        "acknowledged_percent": round(((total_alerts - unack) / total_alerts) * 100, 1) if total_alerts else 0.0,
    }


def get_schedule_summary(days: int = 7) -> Optional[Dict[str, Any]]:
    """Get schedule summary for specified days."""
    data = api_call(f"/schedule/summary?days={days}")
    if isinstance(data, dict) and data:
        return data
    schedule = get_maintenance_schedule(days=days)
    return {
        "total_jobs": len(schedule),
        "scheduled": sum(1 for job in schedule if job.get("status") == "scheduled"),
        "in_progress": sum(1 for job in schedule if job.get("status") == "in_progress"),
        "completed": sum(1 for job in schedule if job.get("status") == "completed"),
        "total_cost": sum(_coerce_float(job.get("estimated_cost"), 0.0) for job in schedule),
        "days": days,
    }


def get_sample_fleet_overview() -> List[Dict[str, Any]]:
    """Generate sample fleet overview data for demo."""
    return [
        _normalize_fleet_item(_default_equipment("EXC-01")),
        _normalize_fleet_item(_default_equipment("DMP-03")),
        _normalize_fleet_item(_default_equipment("CVR-01")),
    ]


def get_sample_alerts() -> List[Dict[str, Any]]:
    """Generate sample alert data for demo."""
    now = datetime.now()
    return [
        {
            "id": 1,
            "equipment_id": "EXC-01",
            "severity": "critical",
            "message": "Hydraulic pump cavitation risk detected.",
            "triggered_at": (now - timedelta(minutes=18)).isoformat(),
            "top_sensors": EQUIPMENT_DEFAULTS["EXC-01"]["top_features"],
            "failure_mode_hint": EQUIPMENT_DEFAULTS["EXC-01"]["failure_mode_hint"],
            "acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
        },
        {
            "id": 2,
            "equipment_id": "DMP-03",
            "severity": "warning",
            "message": "Turbocharger bearing degradation trend increasing.",
            "triggered_at": (now - timedelta(hours=2)).isoformat(),
            "top_sensors": EQUIPMENT_DEFAULTS["DMP-03"]["top_features"],
            "failure_mode_hint": EQUIPMENT_DEFAULTS["DMP-03"]["failure_mode_hint"],
            "acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
        },
    ]


def get_sample_schedule() -> List[Dict[str, Any]]:
    """Generate sample maintenance schedule for demo."""
    now = datetime.now()
    defaults = [EQUIPMENT_DEFAULTS["EXC-01"], EQUIPMENT_DEFAULTS["DMP-03"], EQUIPMENT_DEFAULTS["CVR-01"]]
    schedule: List[Dict[str, Any]] = []
    for index, equipment in enumerate(defaults, start=1):
        start = now + timedelta(hours=(index - 1) * 12)
        end = start + timedelta(hours=equipment["estimated_duration_hours"])
        schedule.append(
            {
                "id": index,
                "equipment_id": equipment["id"],
                "priority_tier": equipment["status"],
                "priority_score": round(equipment["failure_prob"], 2),
                "recommended_action": equipment["recommended_action"],
                "estimated_duration_hours": equipment["estimated_duration_hours"],
                "scheduled_window_start": start.isoformat(),
                "scheduled_window_end": end.isoformat(),
                "status": "scheduled",
                "failure_prob": equipment["failure_prob"],
                "rul_hours": equipment["rul_hours"],
                "estimated_cost": equipment["estimated_cost"],
                "assigned_team": f"Team {chr(64 + index)}",
            }
        )
    schedule.sort(key=lambda job: (-_status_rank(job["priority_tier"]), -job["priority_score"]))
    return schedule
