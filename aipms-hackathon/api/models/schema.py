"""
AIPMS Pydantic Schemas
Request/response schemas for FastAPI validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class EquipmentResponse(BaseModel):
    """Equipment response model"""
    id: str
    name: str
    type: str
    status: str
    last_updated: datetime
    
    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    """Alert response model"""
    id: int
    equipment_id: str
    message: str
    severity: str
    triggered_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    """Prediction response model"""
    equipment_id: str
    timestamp: datetime
    anomaly_score: Optional[float] = None
    anomaly_label: Optional[str] = None
    failure_prob: Optional[float] = None
    rul_hours: Optional[float] = None
    rul_confidence_low: Optional[float] = None
    rul_confidence_high: Optional[float] = None
    top_features_json: Optional[str] = None
    
    class Config:
        from_attributes = True

class MaintenanceJobResponse(BaseModel):
    """Maintenance job response model"""
    id: int
    equipment_id: str
    priority_tier: str
    recommended_action: str
    estimated_duration_hours: float
    scheduled_window_start: datetime
    scheduled_window_end: datetime
    status: str
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    """System health check response"""
    status: str
    api: str
    db: str
    mqtt_broker: str
    uptime_sec: float
    last_inference: Optional[datetime] = None
