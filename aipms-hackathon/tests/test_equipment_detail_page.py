from datetime import datetime

import pandas as pd

from dashboard.api_client import (
    get_equipment_detail,
    get_equipment_rul,
    get_equipment_sensors,
)
from dashboard.pages import equipment_detail


def test_normalize_equipment_detail_handles_api_client_fallback_shape():
    raw_detail = get_equipment_detail("Compressor-1")

    normalized = equipment_detail.normalize_equipment_detail("Compressor-1", raw_detail)

    assert normalized["name"] == "Compressor-1"
    assert normalized["location"]
    assert normalized["status"] in {"Healthy", "Warning", "Critical"}
    assert isinstance(normalized["last_maintenance"], datetime)
    assert isinstance(normalized["next_maintenance"], datetime)
    assert "current_rul_days" in normalized


def test_normalize_sensor_trends_handles_api_client_fallback_shape():
    raw_sensors = get_equipment_sensors("Compressor-1")

    normalized = equipment_detail.normalize_sensor_trends("Compressor-1", raw_sensors)

    assert isinstance(normalized, pd.DataFrame)
    assert set(["timestamp", "temperature", "pressure", "vibration", "rpm"]).issubset(normalized.columns)
    assert not normalized.empty


def test_normalize_rul_degradation_handles_api_client_fallback_shape():
    raw_rul = get_equipment_rul("Compressor-1")

    normalized = equipment_detail.normalize_rul_degradation("Compressor-1", raw_rul)

    assert isinstance(normalized, pd.DataFrame)
    assert set(["date", "rul", "threshold_warning", "threshold_critical"]).issubset(normalized.columns)
    assert not normalized.empty
