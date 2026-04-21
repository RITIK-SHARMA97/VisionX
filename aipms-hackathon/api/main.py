"""
FastAPI application for AIPMS (AI-Powered Predictive Maintenance System).

Provides REST endpoints for:
- Data loading and feature engineering
- Anomaly detection
- Failure prediction
- Remaining Useful Life (RUL) estimation
- Model management and persistence

The API serves as the interface between the trained ML models and external applications.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

import config_constants as cfg
from api.orm import Base

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=cfg.LOG_LEVEL,
    format=cfg.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# ============================================================================
# Application Initialization
# ============================================================================

app = FastAPI(
    title="AIPMS API",
    description="AI-Powered Predictive Maintenance System API",
    version="1.0.0"
)

_phase6_data_module = None
_operational_cache: Dict[str, Dict[str, Any]] = {}
_OPERATIONAL_CACHE_TTL_SECONDS = 5.0

# ============================================================================
# Session State - Not Global
# ============================================================================
# Using FastAPI's dependency injection pattern instead of global state

class AIModel:
    """Dependency injection container for ML models."""
    
    def __init__(self) -> None:
        self.dataset_manager: Optional[Any] = None
        self.feature_engineer: Optional[Any] = None
        self.anomaly_detector: Optional[Any] = None
        self.failure_predictor: Optional[Any] = None
        self.rul_estimator: Optional[Any] = None
        self.X_engineered: Optional[np.ndarray] = None
        self.y_raw: Optional[np.ndarray] = None
        self.X_raw: Optional[np.ndarray] = None
    
    def clear(self) -> None:
        """Clear all cached models and data."""
        self.dataset_manager = None
        self.feature_engineer = None
        self.anomaly_detector = None
        self.failure_predictor = None
        self.rul_estimator = None
        self.X_engineered = None
        self.y_raw = None
        self.X_raw = None
        logger.info("All models and data cleared from cache")

# Global instance - used as dependency
_models = AIModel()

# ============================================================================
# Dependency Injection Functions
# ============================================================================

def get_models() -> AIModel:
    """Get the current AIModel instance (dependency injection)."""
    return _models

# ============================================================================
# Request/Response Models
# ============================================================================

class LoadDataRequest(BaseModel):
    """Request model for data loading."""
    dataset: str = "FD001"
    use_synthetic: bool = True


class FeatureEngineerRequest(BaseModel):
    """Request model for feature engineering."""
    pass  # No parameters needed


class PredictionRequest(BaseModel):
    """Request model for predictions."""
    X: List[List[float]]


class MetricsRequest(BaseModel):
    """Request model for metrics computation."""
    X: List[List[float]]
    y: List[float]


class AnomalyTrainRequest(BaseModel):
    """Request model for anomaly detector training."""
    contamination: float = 0.1


class FailureTrainRequest(BaseModel):
    """Request model for failure predictor training."""
    max_depth: int = 5
    learning_rate: float = 0.05
    n_estimators: int = 300
    threshold: float = 0.5


class RULTrainRequest(BaseModel):
    """Request model for RUL estimator training."""
    sequence_length: int = 30
    lstm_units: int = 64
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 50


class SaveModelsRequest(BaseModel):
    """Request model for saving models."""
    path: str = "/tmp/aipms_models"


class AlertAcknowledgeRequest(BaseModel):
    """Request model for alert acknowledgement."""
    acknowledged_by: str = "demo_user"


def _load_phase6_data_module():
    """Import dashboard data helpers lazily to avoid circular imports at startup."""
    global _phase6_data_module
    if _phase6_data_module is None:
        from dashboard import api_client as dashboard_data

        _phase6_data_module = dashboard_data
    return _phase6_data_module


def _db_path() -> Path:
    return Path(__file__).resolve().parents[1] / cfg.DB_PATH


def _sqlite_count(table_name: str) -> int:
    db_path = _db_path()
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def _sqlite_rows(query: str, params: tuple[Any, ...] = ()) -> List[sqlite3.Row]:
    db_path = _db_path()
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path, timeout=0.2)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def _latest_prediction_summary() -> Dict[str, bool]:
    return {
        "anomaly_detector": get_models().anomaly_detector is not None,
        "failure_predictor": get_models().failure_predictor is not None,
        "rul_estimator": get_models().rul_estimator is not None,
    }


def _get_cached_value(cache_key: str) -> Optional[Any]:
    cached = _operational_cache.get(cache_key)
    if not cached:
        return None
    age_seconds = (datetime.now() - cached["timestamp"]).total_seconds()
    if age_seconds > _OPERATIONAL_CACHE_TTL_SECONDS:
        _operational_cache.pop(cache_key, None)
        return None
    return cached["value"]


def _set_cached_value(cache_key: str, value: Any) -> Any:
    _operational_cache[cache_key] = {
        "timestamp": datetime.now(),
        "value": value,
    }
    return value


def _clear_cache_prefix(prefix: str) -> None:
    for cache_key in list(_operational_cache.keys()):
        if cache_key.startswith(prefix):
            _operational_cache.pop(cache_key, None)


@app.on_event("startup")
async def preload_phase6_dependencies() -> None:
    """Warm the Phase 6 operational data helpers for low-latency first requests."""
    _load_phase6_data_module()
    Base.metadata.create_all(
        create_engine(f"sqlite:///{_db_path()}", connect_args={"check_same_thread": False})
    )
    _seed_phase6_operational_data()


def _seed_phase6_operational_data() -> None:
    """Populate baseline demo records when predictions and jobs are empty."""
    dashboard_data = _load_phase6_data_module()
    db_path = _db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        if _sqlite_count("equipment") == 0:
            for equipment in dashboard_data.get_sample_fleet_overview():
                cursor.execute(
                    """
                    INSERT INTO equipment (
                        id, name, type, location, total_operating_hours, status, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        equipment["id"],
                        equipment["name"],
                        equipment["type"],
                        equipment["location"],
                        equipment["total_operating_hours"],
                        equipment["status"],
                        equipment["last_updated"],
                    ),
                )

        if _sqlite_count("predictions") == 0:
            for equipment in dashboard_data.get_sample_fleet_overview():
                cursor.execute(
                    """
                    INSERT INTO predictions (
                        equipment_id, timestamp, anomaly_score, anomaly_label, failure_prob,
                        rul_hours, rul_confidence_low, rul_confidence_high, top_features_json, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        equipment["id"],
                        datetime.now().isoformat(),
                        equipment["anomaly_score"],
                        equipment["status"],
                        equipment["failure_prob"],
                        equipment["rul_hours"],
                        max(0.0, equipment["rul_hours"] - 18),
                        equipment["rul_hours"] + 24,
                        json.dumps(equipment["top_features"]),
                        "phase6-demo",
                    ),
                )

        if _sqlite_count("alerts") == 0:
            for alert in dashboard_data.get_sample_alerts():
                cursor.execute(
                    """
                    INSERT INTO alerts (
                        id, equipment_id, triggered_at, severity, message, top_sensors,
                        failure_mode_hint, acknowledged, acknowledged_at, acknowledged_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert["id"],
                        alert["equipment_id"],
                        alert["triggered_at"],
                        alert["severity"],
                        alert["message"],
                        json.dumps(alert["top_sensors"]),
                        alert["failure_mode_hint"],
                        int(bool(alert["acknowledged"])),
                        alert["acknowledged_at"],
                        alert["acknowledged_by"],
                    ),
                )

        if _sqlite_count("maintenance_jobs") == 0:
            for job in dashboard_data.get_sample_schedule():
                cursor.execute(
                    """
                    INSERT INTO maintenance_jobs (
                        id, equipment_id, created_at, priority_score, priority_tier, failure_prob,
                        rul_hours, recommended_action, estimated_duration_hours,
                        scheduled_window_start, scheduled_window_end, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job["id"],
                        job["equipment_id"],
                        datetime.now().isoformat(),
                        job["priority_score"],
                        job["priority_tier"],
                        job["failure_prob"],
                        job["rul_hours"],
                        job["recommended_action"],
                        job["estimated_duration_hours"],
                        job["scheduled_window_start"],
                        job["scheduled_window_end"],
                        job["status"],
                        f"Assigned team: {job.get('assigned_team', 'Team A')}",
                    ),
                )

        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Health Endpoints
# ============================================================================

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint - health check."""
    logger.info("Root health check called")
    return {
        "status": "healthy",
        "service": "AIPMS API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health endpoint."""
    logger.debug("Health check called")
    services = {
        "api": "ok",
        "database": "ok" if _db_path().exists() else "degraded",
        "mqtt": "unknown",
        "dashboard": "unknown",
    }
    return {
        "api": "ok",
        "status": "healthy",
        "timestamp": str(np.datetime64("now"))
        ,
        "services": services,
        "models": _latest_prediction_summary(),
    }


@app.get("/equipment")
async def get_equipment() -> List[Dict[str, Any]]:
    """Return the Phase 6 fleet overview contract."""
    cached = _get_cached_value("equipment")
    if cached is not None:
        return cached

    dashboard_data = _load_phase6_data_module()
    equipment_rows = _sqlite_rows(
        """
        SELECT id, name, type, location, total_operating_hours, status, last_updated
        FROM equipment
        ORDER BY id
        """
    )
    if not equipment_rows:
        return _set_cached_value("equipment", dashboard_data.get_sample_fleet_overview())

    prediction_rows = _sqlite_rows(
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
    latest_predictions = {row["equipment_id"]: dict(row) for row in prediction_rows}

    fleet: List[Dict[str, Any]] = []
    for row in equipment_rows:
        default = dashboard_data._default_equipment(row["id"])
        item = {
            **default,
            "id": row["id"],
            "name": row["name"] or default["name"],
            "type": row["type"] or default["type"],
            "location": row["location"] or default["location"],
            "status": row["status"] or default["status"],
            "total_operating_hours": row["total_operating_hours"] or default["total_operating_hours"],
            "last_updated": row["last_updated"] or default["last_updated"],
        }
        prediction = latest_predictions.get(row["id"])
        if prediction:
            top_features = prediction.get("top_features_json")
            if isinstance(top_features, str):
                try:
                    top_features = json.loads(top_features)
                except json.JSONDecodeError:
                    top_features = default["top_features"]
            item.update(
                {
                    "anomaly_score": float(prediction.get("anomaly_score", default["anomaly_score"])),
                    "failure_prob": float(prediction.get("failure_prob", default["failure_prob"])),
                    "rul_hours": float(prediction.get("rul_hours", default["rul_hours"])),
                    "status": prediction.get("anomaly_label", item["status"]),
                    "top_features": top_features or default["top_features"],
                }
            )
        fleet.append(item)

    fleet.sort(key=lambda equipment: (-dashboard_data._status_rank(equipment["status"]), equipment["id"]))
    return _set_cached_value("equipment", fleet)


@app.get("/equipment/{equipment_id}")
async def get_equipment_detail(equipment_id: str) -> Dict[str, Any]:
    """Return detailed operational data for one equipment unit."""
    dashboard_data = _load_phase6_data_module()
    fleet = await get_equipment()
    equipment = next((item for item in fleet if item["id"] == equipment_id), None)
    if equipment is None:
        equipment = dashboard_data._default_equipment(equipment_id)

    latest_rul = await get_equipment_rul(equipment_id)
    detail = {
        **equipment,
        "predictions": await get_equipment_predictions(equipment_id, days=30),
        "sensors": await get_equipment_sensors(equipment_id, limit=50),
        "rul": latest_rul,
    }
    return detail


@app.get("/equipment/{equipment_id}/sensors")
async def get_equipment_sensors(equipment_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent sensor readings for an equipment unit."""
    dashboard_data = _load_phase6_data_module()
    rows = dashboard_data._sqlite_query(
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
    return dashboard_data._sample_sensor_rows(equipment_id, limit)


@app.get("/equipment/{equipment_id}/predictions")
async def get_equipment_predictions(equipment_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Return historical predictions for an equipment unit."""
    dashboard_data = _load_phase6_data_module()
    rows = dashboard_data._sqlite_query(
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
        history = []
        for row in reversed(rows):
            item = dict(row)
            raw_top_features = item.get("top_features_json")
            if isinstance(raw_top_features, str):
                try:
                    item["top_features_json"] = json.loads(raw_top_features)
                except json.JSONDecodeError:
                    pass
            history.append(item)
        return history
    return dashboard_data._sample_prediction_history(equipment_id, days=min(days, 30))


@app.get("/equipment/{equipment_id}/rul")
async def get_equipment_rul(equipment_id: str) -> Dict[str, Any]:
    """Return the latest RUL snapshot."""
    history = await get_equipment_predictions(equipment_id, days=30)
    latest = history[-1]
    return {
        "rul_hours": float(latest["rul_hours"]),
        "rul_cycles": round(float(latest["rul_hours"]) * 3.6),
        "ci_low": float(latest.get("rul_confidence_low", max(0.0, float(latest["rul_hours"]) - 18))),
        "ci_high": float(latest.get("rul_confidence_high", float(latest["rul_hours"]) + 24)),
        "staleness_flag": False,
    }


@app.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    days: int = 7,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return current or historical alerts."""
    cache_key = f"alerts:{severity}:{acknowledged}:{days}:{start_date}:{end_date}"
    cached = _get_cached_value(cache_key)
    if cached is not None:
        return cached

    dashboard_data = _load_phase6_data_module()
    rows = _sqlite_rows(
        """
        SELECT id, equipment_id, triggered_at, severity, message, top_sensors,
               failure_mode_hint, acknowledged, acknowledged_at, acknowledged_by
        FROM alerts
        ORDER BY triggered_at DESC
        """
    )
    alerts = [dict(row) for row in rows]
    for alert in alerts:
        raw_top_sensors = alert.get("top_sensors")
        if isinstance(raw_top_sensors, str):
            try:
                alert["top_sensors"] = json.loads(raw_top_sensors)
            except json.JSONDecodeError:
                pass
    if not alerts:
        alerts = dashboard_data.get_sample_alerts()

    if start_date or end_date:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        filtered = []
        for alert in alerts:
            alert_dt = dashboard_data._parse_timestamp(alert.get("triggered_at"), datetime.now())
            if start_dt and alert_dt.date() < start_dt.date():
                continue
            if end_dt and alert_dt.date() > end_dt.date():
                continue
            filtered.append(alert)
        alerts = filtered
    elif days:
        cutoff = datetime.now() - timedelta(days=days)
        alerts = [
            alert for alert in alerts
            if dashboard_data._parse_timestamp(alert.get("triggered_at"), datetime.now()) >= cutoff
        ]

    if severity:
        alerts = [alert for alert in alerts if str(alert.get("severity", "")).lower() == severity.lower()]
    if acknowledged is not None:
        alerts = [alert for alert in alerts if bool(alert.get("acknowledged")) == acknowledged]

    return _set_cached_value(cache_key, alerts)


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, request: AlertAcknowledgeRequest) -> Dict[str, Any]:
    """Acknowledge an alert and return audit details."""
    timestamp = datetime.now().isoformat()
    db_path = _db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE alerts
            SET acknowledged = 1,
                acknowledged_by = ?,
                acknowledged_at = ?
            WHERE id = ?
            """,
            (request.acknowledged_by, timestamp, alert_id),
        )
        conn.commit()
    finally:
        conn.close()
    _clear_cache_prefix("alerts:")
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_by": request.acknowledged_by,
        "acknowledged_at": timestamp,
    }


@app.get("/alerts/stats")
async def get_alert_stats() -> Dict[str, Any]:
    """Return aggregate alert counters for dashboard widgets."""
    alerts = await get_alerts(days=7)
    total_alerts = len(alerts)
    unack = sum(1 for alert in alerts if not alert.get("acknowledged"))
    critical = sum(1 for alert in alerts if str(alert.get("severity")).lower() == "critical")
    return {
        "total_alerts": total_alerts,
        "unacknowledged": unack,
        "critical": critical,
        "high": sum(1 for alert in alerts if str(alert.get("severity")).lower() in {"critical", "warning"}),
        "acknowledged_percent": round(((total_alerts - unack) / total_alerts) * 100, 1) if total_alerts else 0.0,
    }


@app.get("/schedule")
async def get_schedule(days: int = 7) -> List[Dict[str, Any]]:
    """Return maintenance schedule entries."""
    cache_key = f"schedule:{days}"
    cached = _get_cached_value(cache_key)
    if cached is not None:
        return cached

    dashboard_data = _load_phase6_data_module()
    rows = _sqlite_rows(
        """
        SELECT id, equipment_id, created_at, priority_score, priority_tier, failure_prob,
               rul_hours, recommended_action, estimated_duration_hours,
               scheduled_window_start, scheduled_window_end, status, notes
        FROM maintenance_jobs
        ORDER BY priority_score DESC, created_at ASC
        """
    )
    if rows:
        return _set_cached_value(cache_key, [dict(row) for row in rows])
    return _set_cached_value(cache_key, dashboard_data.get_sample_schedule())


@app.get("/schedule/summary")
async def get_schedule_summary(days: int = 7) -> Dict[str, Any]:
    """Return schedule summary KPI values."""
    schedule = await get_schedule(days=days)
    return {
        "total_jobs": len(schedule),
        "scheduled": sum(1 for job in schedule if job.get("status") == "scheduled"),
        "in_progress": sum(1 for job in schedule if job.get("status") == "in_progress"),
        "completed": sum(1 for job in schedule if job.get("status") == "completed"),
        "total_cost": sum(float(job.get("estimated_cost", 0.0)) for job in schedule),
        "days": days,
    }


@app.get("/dashboard/kpi")
async def get_dashboard_kpi() -> Dict[str, Any]:
    """Return top-level KPI data for the dashboard."""
    fleet = await get_equipment()
    alerts = await get_alerts(days=7)
    schedule = await get_schedule(days=7)
    total_cost = sum(float(job.get("estimated_cost", 0.0)) for job in schedule)
    return {
        "total_equipment": len(fleet),
        "critical_count": sum(1 for equipment in fleet if equipment["status"] == "critical"),
        "warning_count": sum(1 for equipment in fleet if equipment["status"] == "warning"),
        "normal_count": sum(1 for equipment in fleet if equipment["status"] == "normal"),
        "alerts_today": sum(
            1 for alert in alerts if _load_phase6_data_module()._parse_timestamp(alert["triggered_at"]).date() == datetime.now().date()
        ),
        "estimated_cost_7day": total_cost,
        "average_failure_probability": round(
            sum(float(equipment["failure_prob"]) for equipment in fleet) / len(fleet), 3
        ) if fleet else 0.0,
    }


@app.get("/dashboard/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """Return lightweight dashboard summary data."""
    return {
        "fleet": await get_equipment(),
        "kpi": await get_dashboard_kpi(),
        "alerts": await get_alerts(days=1),
        "generated_at": datetime.now().isoformat(),
    }


# ============================================================================
# Data Endpoints
# ============================================================================

@app.post("/data/load")
async def load_dataset(request: LoadDataRequest) -> Dict[str, Any]:
    """Load dataset."""
    try:
        logger.info(f"Loading dataset: {request.dataset}, synthetic={request.use_synthetic}")
        from models.train.data_manager import DatasetManager
        
        dm = DatasetManager()
        X_raw, y_raw = dm.load(request.dataset, use_synthetic=request.use_synthetic)
        
        models = get_models()
        models.dataset_manager = dm
        models.X_raw = X_raw
        models.y_raw = y_raw
        
        logger.info(f"Dataset loaded: {X_raw.shape[0]} samples, {X_raw.shape[1]} features")
        
        return {
            "status": "loaded",
            "dataset": request.dataset,
            "n_samples": len(X_raw),
            "n_features": X_raw.shape[1]
        }
    except Exception as e:
        logger.error(f"Error loading dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/features/engineer")
async def engineer_features(request: FeatureEngineerRequest) -> Dict[str, Any]:
    """Engineer features from raw data."""
    try:
        models = get_models()
        
        if models.X_raw is None:
            logger.warning("Feature engineering attempted without raw data")
            raise ValueError("No raw data loaded. Call /data/load first.")
        
        logger.info("Starting feature engineering")
        from models.train.feature_engineer import FeatureEngineer
        
        fe = FeatureEngineer()
        X_engineered = fe.process(models.X_raw)
        
        models.feature_engineer = fe
        models.X_engineered = X_engineered
        
        logger.info(f"Features engineered: {X_engineered.shape[0]} samples, {X_engineered.shape[1]} features")
        
        return {
            "status": "engineered",
            "n_samples": len(X_engineered),
            "n_features": X_engineered.shape[1]
        }
    except Exception as e:
        logger.error(f"Error in feature engineering: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================

@app.post("/anomaly/train")
async def train_anomaly_detector(request: AnomalyTrainRequest) -> Dict[str, Any]:
    """Train anomaly detector."""
    try:
        models = get_models()
        
        if models.X_engineered is None:
            logger.warning("Anomaly detector training attempted without engineered features")
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        logger.info(f"Training anomaly detector with contamination={request.contamination}")
        from models.train.anomaly_detector import AnomalyDetector
        
        ad = AnomalyDetector(contamination=request.contamination)
        ad.fit(models.X_engineered)
        
        models.anomaly_detector = ad
        logger.info("Anomaly detector training complete")
        
        return {
            "status": "trained",
            "model": "AnomalyDetector",
            "contamination": request.contamination
        }
    except Exception as e:
        logger.error(f"Error training anomaly detector: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/anomaly/predict")
async def predict_anomaly(request: PredictionRequest) -> Dict[str, Any]:
    """Predict anomalies."""
    models = get_models()
    
    if models.anomaly_detector is None:
        logger.warning("Anomaly prediction attempted without trained model")
        raise HTTPException(status_code=400, detail="Anomaly detector not trained. Call /anomaly/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        logger.debug(f"Predicting anomalies for {len(X)} samples")
        labels, scores = models.anomaly_detector.predict_with_scores(X)
        
        return {
            "predictions": labels.tolist(),
            "scores": scores.tolist(),
            "n_samples": len(labels)
        }
    except Exception as e:
        logger.error(f"Error predicting anomalies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Failure Prediction Endpoints
# ============================================================================

@app.post("/failure/train")
async def train_failure_predictor(request: FailureTrainRequest) -> Dict[str, Any]:
    """Train failure predictor."""
    try:
        models = get_models()
        
        if models.X_engineered is None:
            logger.warning("Failure predictor training attempted without engineered features")
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        logger.info(f"Training failure predictor: max_depth={request.max_depth}, learning_rate={request.learning_rate}")
        from models.train.failure_predictor import FailurePredictor
        
        # Create labels (RUL <= 30 cycles = failure)
        window_size = 5
        y_failure = (models.y_raw[window_size-1:] <= 30).astype(int)
        X = models.X_engineered
        
        if len(y_failure) != len(X):
            raise ValueError(f"Label mismatch: {len(y_failure)} vs {len(X)}")
        
        fp = FailurePredictor(
            max_depth=request.max_depth,
            learning_rate=request.learning_rate,
            n_estimators=request.n_estimators,
            threshold=request.threshold
        )
        fp.fit(X, y_failure)
        
        models.failure_predictor = fp
        logger.info("Failure predictor training complete")
        
        return {
            "status": "trained",
            "model": "FailurePredictor",
            "max_depth": request.max_depth,
            "learning_rate": request.learning_rate
        }
    except Exception as e:
        logger.error(f"Error training failure predictor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/predict")
async def predict_failure(request: PredictionRequest) -> Dict[str, Any]:
    """Predict binary failure."""
    models = get_models()
    
    if models.failure_predictor is None:
        logger.warning("Failure prediction attempted without trained model")
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        logger.debug(f"Predicting failures for {len(X)} samples")
        preds = models.failure_predictor.predict(X)
        
        return {
            "predictions": preds.tolist(),
            "n_samples": len(preds)
        }
    except Exception as e:
        logger.error(f"Error predicting failures: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/predict_proba")
async def predict_failure_proba(request: PredictionRequest) -> Dict[str, Any]:
    """Predict failure probability."""
    models = get_models()
    
    if models.failure_predictor is None:
        logger.warning("Failure probability prediction attempted without trained model")
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        logger.debug(f"Predicting failure probabilities for {len(X)} samples")
        proba = models.failure_predictor.predict_proba(X)
        
        return {
            "probabilities": proba.tolist(),
            "n_samples": len(proba)
        }
    except Exception as e:
        logger.error(f"Error predicting failure probabilities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/shap_values")
async def get_failure_shap_values(request: PredictionRequest) -> Dict[str, Any]:
    """Get SHAP feature importance."""
    models = get_models()
    
    if models.failure_predictor is None:
        logger.warning("SHAP values requested without trained model")
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        logger.debug(f"Computing SHAP values for {len(X)} samples")
        shap_vals = models.failure_predictor.get_shap_values(X)
        
        return {
            "shap_values": shap_vals.tolist(),
            "n_samples": len(shap_vals),
            "n_features": shap_vals.shape[1]
        }
    except Exception as e:
        logger.error(f"Error computing SHAP values: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/metrics")
async def compute_failure_metrics(request: MetricsRequest) -> Dict[str, Any]:
    """Compute failure prediction metrics."""
    models = get_models()
    
    if models.failure_predictor is None:
        logger.warning("Failure metrics requested without trained model")
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        y = np.array(request.y, dtype=np.float32)
        
        logger.debug(f"Computing failure metrics for {len(X)} samples")
        
        # Convert continuous y to binary labels (0 or 1)
        # If y is already binary, this won't change anything
        # If y is continuous, threshold at 0.5
        y_binary = (y > 0.5).astype(int) if np.max(y) <= 1.0 else (y > np.median(y)).astype(int)
        
        metrics = models.failure_predictor.compute_metrics(X, y_binary)
        
        # Ensure all values are JSON-serializable floats
        metrics_clean = {k: float(v) for k, v in metrics.items()}
        
        return metrics_clean
    except Exception as e:
        logger.error(f"Error computing failure metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUL Estimation Endpoints
# ============================================================================

@app.post("/rul/train")
async def train_rul_estimator(request: RULTrainRequest) -> Dict[str, Any]:
    """Train RUL estimator."""
    try:
        models = get_models()
        
        if models.X_engineered is None:
            logger.warning("RUL estimator training attempted without engineered features")
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        logger.info(f"Training RUL estimator: lstm_units={request.lstm_units}, epochs={request.epochs}")
        from models.train.rul_estimator import RULEstimator
        
        # Create RUL labels (y_raw is already RUL in cycles)
        window_size = 5
        y_rul = models.y_raw[window_size-1:].astype(np.float32)
        X = models.X_engineered
        
        if len(y_rul) != len(X):
            raise ValueError(f"Label mismatch: {len(y_rul)} vs {len(X)}")
        
        rul = RULEstimator(
            sequence_length=request.sequence_length,
            lstm_units=request.lstm_units,
            dropout_rate=request.dropout_rate,
            learning_rate=request.learning_rate,
            epochs=request.epochs
        )
        rul.fit(X, y_rul, validation_split=0.2, verbose=0)
        
        models.rul_estimator = rul
        logger.info("RUL estimator training complete")
        
        return {
            "status": "trained",
            "model": "RULEstimator",
            "sequence_length": request.sequence_length,
            "lstm_units": request.lstm_units,
            "epochs": request.epochs
        }
    except Exception as e:
        logger.error(f"Error training RUL estimator: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rul/predict")
async def predict_rul(request: PredictionRequest) -> Dict[str, Any]:
    """Predict RUL."""
    models = get_models()
    
    if models.rul_estimator is None:
        logger.warning("RUL prediction attempted without trained model")
        raise HTTPException(status_code=400, detail="RUL estimator not trained. Call /rul/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        logger.debug(f"Predicting RUL for {len(X)} samples")
        rul_est = models.rul_estimator
        
        # If input is smaller than sequence_length, pad it with zeros
        if X.shape[0] < rul_est.sequence_length:
            X_padded = np.zeros((rul_est.sequence_length, X.shape[1]), dtype=np.float32)
            X_padded[-X.shape[0]:] = X
            X = X_padded
        
        preds = rul_est.predict(X)
        
        # Handle empty predictions
        if preds is None or len(preds) == 0:
            # Return dummy predictions if model returns empty
            preds = np.zeros(len(request.X), dtype=np.float32)
        
        # Return only predictions for the original input size
        preds = preds[:len(request.X)]
        
        return {
            "predictions": preds.tolist(),
            "n_samples": len(preds)
        }
    except Exception as e:
        logger.error(f"Error predicting RUL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rul/metrics")
async def compute_rul_metrics(request: MetricsRequest) -> Dict[str, Any]:
    """Compute RUL metrics."""
    models = get_models()
    
    if models.rul_estimator is None:
        logger.warning("RUL metrics requested without trained model")
        raise HTTPException(status_code=400, detail="RUL estimator not trained. Call /rul/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        y = np.array(request.y, dtype=np.float32)
        
        logger.debug(f"Computing RUL metrics for {len(X)} samples")
        metrics = models.rul_estimator.compute_metrics(X, y)
        
        # Ensure all values are JSON-serializable floats
        metrics_clean = {k: float(v) for k, v in metrics.items()}
        
        return metrics_clean
    except Exception as e:
        logger.error(f"Error computing RUL metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Model Management Endpoints
# ============================================================================

@app.post("/models/save")
async def save_models(request: SaveModelsRequest) -> Dict[str, Any]:
    """Save all trained models."""
    try:
        models = get_models()
        path = Path(request.path)
        path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving models to {path}")
        saved = []
        
        if models.anomaly_detector is not None:
            models.anomaly_detector.save(str(path / "anomaly_detector"))
            saved.append("anomaly_detector")
            logger.debug("Saved anomaly_detector")
        
        if models.failure_predictor is not None:
            models.failure_predictor.save(str(path / "failure_predictor"))
            saved.append("failure_predictor")
            logger.debug("Saved failure_predictor")
        
        if models.rul_estimator is not None:
            models.rul_estimator.save(str(path / "rul_estimator"))
            saved.append("rul_estimator")
            logger.debug("Saved rul_estimator")
        
        logger.info(f"Models saved successfully: {saved}")
        
        return {
            "status": "saved",
            "path": str(path),
            "models": saved
        }
    except Exception as e:
        logger.error(f"Error saving models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Get status of all models."""
    models = get_models()
    logger.debug("Retrieving models status")
    
    return {
        "anomaly_detector": {
            "trained": models.anomaly_detector is not None
        },
        "failure_predictor": {
            "trained": models.failure_predictor is not None
        },
        "rul_estimator": {
            "trained": models.rul_estimator is not None
        },
        "data_loaded": models.X_engineered is not None
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting AIPMS API on {cfg.API_HOST}:{cfg.API_PORT}")
    uvicorn.run(app, host=cfg.API_HOST, port=cfg.API_PORT)
