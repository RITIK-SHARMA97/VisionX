"""
AIPMS ORM Models
SQLAlchemy table definitions
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Equipment(Base):
    """Equipment table - represents mining equipment units"""
    __tablename__ = "equipment"
    
    id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    location = Column(String(100))
    status = Column(String(10), default='normal')
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SensorReading(Base):
    """Sensor readings table - raw telemetry from MQTT"""
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(10), ForeignKey('equipment.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sensor_name = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    data_quality_flag = Column(String(10), default='ok')

class Prediction(Base):
    """Predictions table - ML model outputs"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(10), ForeignKey('equipment.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    anomaly_score = Column(Float)
    anomaly_label = Column(String(10))
    failure_prob = Column(Float)
    rul_hours = Column(Float)
    rul_confidence_low = Column(Float)
    rul_confidence_high = Column(Float)
    top_features_json = Column(Text)
    model_version = Column(String(20))

class Alert(Base):
    """Alerts table - actionable notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(10), ForeignKey('equipment.id'), nullable=False)
    triggered_at = Column(DateTime, nullable=False)
    severity = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    top_sensors = Column(Text)
    failure_mode_hint = Column(String(100))
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(50))
    resolved_at = Column(DateTime)

class MaintenanceJob(Base):
    """Maintenance jobs table - scheduled maintenance"""
    __tablename__ = "maintenance_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(10), ForeignKey('equipment.id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    priority_score = Column(Float)
    priority_tier = Column(String(10))
    failure_prob = Column(Float)
    rul_hours = Column(Float)
    recommended_action = Column(Text)
    estimated_duration_hours = Column(Float)
    parts_required = Column(Text)
    scheduled_window_start = Column(DateTime)
    scheduled_window_end = Column(DateTime)
    status = Column(String(20), default='scheduled')
    cmms_work_order_id = Column(String(50))
    notes = Column(Text)

class ModelMetadata(Base):
    """Model metadata table - track model versions and performance"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(50), unique=True, nullable=False)
    version = Column(String(20))
    trained_at = Column(DateTime)
    dataset = Column(String(50))
    n_train_samples = Column(Integer)
    rmse = Column(Float)
    auc_roc = Column(Float)
    f1_score = Column(Float)
    nasa_score = Column(Float)
    feature_list_json = Column(Text)
    hyperparams_json = Column(Text)
    file_path = Column(String(200))
