"""
Pydantic Schema Models for AIPMS API
Request/response validation and documentation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# === Equipment Schemas ===
class EquipmentBase(BaseModel):
    name: str
    type: str
    location: str
    status: str = "normal"


class EquipmentCreate(EquipmentBase):
    id: str


class EquipmentUpdate(BaseModel):
    status: Optional[str] = None
    total_operating_hours: Optional[float] = None


class Equipment(EquipmentBase):
    id: str
    commissioned_date: Optional[datetime]
    total_operating_hours: float
    last_updated: datetime
    
    class Config:
        from_attributes = True


# === Sensor Reading Schemas ===
class SensorReadingBase(BaseModel):
    equipment_id: str
    sensor_name: str
    value: float
    unit: str


class SensorReadingCreate(SensorReadingBase):
    timestamp: datetime


class SensorReading(SensorReadingBase):
    id: int
    timestamp: datetime
    data_quality_flag: str
    
    class Config:
        from_attributes = True


# === Prediction Schemas ===
class PredictionBase(BaseModel):
    equipment_id: str
    anomaly_score: float = Field(ge=0, le=1)
    anomaly_label: str
    failure_prob: float = Field(ge=0, le=1)
    rul_hours: float = Field(ge=0)
    model_version: str


class PredictionCreate(PredictionBase):
    timestamp: datetime
    top_features_json: Optional[List[Dict[str, Any]]] = None
    rul_confidence_low: Optional[float] = None
    rul_confidence_high: Optional[float] = None


class Prediction(PredictionBase):
    id: int
    timestamp: datetime
    top_features_json: Optional[List[Dict[str, Any]]]
    rul_confidence_low: Optional[float]
    rul_confidence_high: Optional[float]
    
    class Config:
        from_attributes = True


# === Alert Schemas ===
class AlertBase(BaseModel):
    equipment_id: str
    severity: str
    message: str


class AlertCreate(AlertBase):
    triggered_at: datetime
    top_sensors: Optional[List[Dict[str, Any]]] = None
    failure_mode_hint: Optional[str] = None


class AlertAcknowledge(BaseModel):
    acknowledged_by: str


class Alert(AlertBase):
    id: int
    triggered_at: datetime
    top_sensors: Optional[List[Dict[str, Any]]]
    failure_mode_hint: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Alias for backward compatibility
MaintenanceAlert = Alert


# === Maintenance Job Schemas ===
class MaintenanceJobBase(BaseModel):
    equipment_id: str
    priority_score: float = Field(ge=0, le=1)
    priority_tier: str
    recommended_action: str
    estimated_duration_hours: float


class MaintenanceJobCreate(MaintenanceJobBase):
    created_at: datetime
    failure_prob: float
    rul_hours: float
    parts_required: Optional[List[Dict[str, Any]]] = None
    scheduled_window_start: Optional[datetime] = None
    scheduled_window_end: Optional[datetime] = None


class MaintenanceJob(MaintenanceJobBase):
    id: int
    created_at: datetime
    failure_prob: float
    rul_hours: float
    parts_required: Optional[List[Dict[str, Any]]]
    scheduled_window_start: Optional[datetime]
    scheduled_window_end: Optional[datetime]
    status: str
    cmms_work_order_id: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# === Health Check Response ===
class HealthCheckResponse(BaseModel):
    status: str
    api: str
    db: str
    mqtt_broker: str
    models: Dict[str, str]
    uptime_sec: float
    timestamp: datetime


# === Fleet Summary ===
class FleetSummary(BaseModel):
    total_equipment: int
    critical_count: int
    warning_count: int
    normal_count: int
    alerts_today: int
    estimated_cost_7day: float
