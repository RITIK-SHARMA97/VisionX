"""
Configuration constants for AIPMS - centralized settings to avoid hardcoded values.

All magic numbers, thresholds, and configuration values are defined here.
Import this module instead of hardcoding values throughout the codebase.
"""

import logging
from typing import Final

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL: Final = logging.INFO
LOG_FORMAT: Final = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================================
# MQTT CONFIGURATION
# ============================================================================

MQTT_BROKER_HOST: Final = "localhost"
MQTT_BROKER_PORT: Final = 1883
MQTT_BROKER_TIMEOUT: Final = 60
MQTT_BROKER_KEEP_ALIVE: Final = 60
MQTT_CLIENT_ID_PREFIX: Final = "aipms"
MQTT_PUBLISH_QOS: Final = 1
MQTT_RECONNECT_DELAY_MIN: Final = 1  # seconds
MQTT_RECONNECT_DELAY_MAX: Final = 30  # seconds
MQTT_MAX_RECONNECT_ATTEMPTS: Final = 5

# ============================================================================
# FEATURE ENGINEERING CONFIGURATION
# ============================================================================

FEATURE_WINDOW_SIZE: Final = 5  # Rolling window for statistics (cycles)
FEATURE_MIN_MAX_SCALE_EPSILON: Final = 1e-8  # Prevent division by zero

# ============================================================================
# MODEL PREDICTION CONFIGURATION
# ============================================================================

# Anomaly Detection
ANOMALY_CONTAMINATION_RATE: Final = 0.05  # 5% of data assumed anomalous
ANOMALY_THRESHOLD_WARNING: Final = 0.40  # Anomaly score threshold for warning
ANOMALY_THRESHOLD_CRITICAL: Final = 0.70  # Anomaly score threshold for critical

# Failure Prediction
FAILURE_PREDICTION_HORIZON_DAYS: Final = 7  # Predict failures 7 days in advance
FAILURE_PREDICTION_HORIZON_CYCLES: Final = 30  # In cycles (C-MAPSS dataset)
FAILURE_PREDICTION_THRESHOLD: Final = 0.70  # Probability threshold for alert

# RUL Estimation
RUL_CLIPPING_MAX: Final = 125  # Max RUL value (cycles) - piecewise linear
RUL_CONFIDENCE_INTERVAL: Final = 0.95  # 95% confidence interval

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_HOST: Final = "0.0.0.0"
API_PORT: Final = 8000
API_WORKERS: Final = 1
API_RELOAD: Final = False
API_HEALTH_CHECK_INTERVAL: Final = 10  # seconds

# Response timeouts (milliseconds)
API_INFERENCE_TIMEOUT_MS: Final = 5000  # 5 seconds for inference
API_DB_QUERY_TIMEOUT_MS: Final = 3000  # 3 seconds for database queries

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_PATH: Final = "aipms.db"
DB_POOL_SIZE: Final = 5
DB_MAX_OVERFLOW: Final = 10
DB_ECHO_SQL: Final = False  # Set to True for debugging

# Data retention
DB_SENSOR_READINGS_RETENTION_DAYS: Final = 90
DB_PREDICTIONS_RETENTION_DAYS: Final = 30
DB_ALERTS_RETENTION_DAYS: Final = 90

# ============================================================================
# DASHBOARD CONFIGURATION
# ============================================================================

DASHBOARD_PORT: Final = 8501
DASHBOARD_REFRESH_INTERVAL_SECONDS: Final = 5
DASHBOARD_API_TIMEOUT_SECONDS: Final = 10
DASHBOARD_CHART_HEIGHT: Final = 400
DASHBOARD_CHART_FONT_SIZE: Final = 12

# ============================================================================
# SENSOR CONFIGURATION
# ============================================================================

SENSOR_PUBLISH_FREQUENCY_HZ: Final = 1  # 1 Hz = 1 reading per second
SENSOR_BUFFER_SIZE_MAX: Final = 10000  # Max readings to buffer before alerting

# ============================================================================
# SCHEDULING CONFIGURATION
# ============================================================================

INFERENCE_SCHEDULE_INTERVAL_SECONDS: Final = 10  # Run inference every 10 seconds
MAINTENANCE_SCHEDULING_INTERVAL_SECONDS: Final = 60  # Update schedule every 60 seconds
HEALTH_CHECK_INTERVAL_SECONDS: Final = 30  # Health check every 30 seconds

# ============================================================================
# EQUIPMENT CONFIGURATION
# ============================================================================

# Equipment types and their sensor specifications
EQUIPMENT_TYPES: Final = {
    "excavator": {
        "sensors": [
            "temperature_block",
            "temperature_hydraulic",
            "temperature_exhaust",
            "pressure_hydraulic",
            "rpm_primary",
            "rpm_secondary",
            "pressure_boost",
            "fuel_consumption",
            "pressure_bleed",
            "speed_deviation"
        ],
        "thresholds": {
            "temperature_warning": 105,
            "temperature_critical": 115,
            "pressure_warning": 160,
            "pressure_critical": 140
        }
    },
    "dumper": {
        "sensors": [
            "engine_temperature",
            "turbo_pressure",
            "rpm",
            "current_draw",
            "fuel_rate",
            "suspension_pressure"
        ],
        "thresholds": {
            "engine_temp_warning": 105,
            "engine_temp_critical": 120,
            "boost_pressure_warning": 1.1,
            "boost_pressure_critical": 0.8
        }
    },
    "conveyor": {
        "sensors": [
            "belt_tension",
            "motor_current",
            "motor_temperature",
            "belt_speed",
            "drift_lateral"
        ],
        "thresholds": {
            "tension_warning": 6,
            "tension_critical": 4,
            "current_warning": 75,
            "current_critical": 90
        }
    }
}

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Input size limits (prevent DoS)
MAX_BATCH_SIZE: Final = 1000
MAX_REQUEST_SIZE_MB: Final = 10
MAX_ARRAY_LENGTH: Final = 100000

# ============================================================================
# MODEL TRAINING CONFIGURATION
# ============================================================================

TRAINING_EPOCHS: Final = 100  # Number of training epochs for neural network models
TRAINING_BATCH_SIZE: Final = 256  # Batch size for training
TRAINING_LEARNING_RATE: Final = 0.05  # Learning rate for gradient descent

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# CORS
ALLOWED_ORIGINS: Final = ["http://localhost:3000", "http://localhost:8501"]
ALLOW_CREDENTIALS: Final = True

# Rate limiting (optional - if using slowapi)
RATE_LIMIT_ENABLED: Final = True
RATE_LIMIT_REQUESTS: Final = 100
RATE_LIMIT_PERIOD_SECONDS: Final = 60

# ============================================================================
# DEBUG/DEVELOPMENT CONFIGURATION
# ============================================================================

DEBUG_MODE: Final = False
VERBOSE_LOGGING: Final = False
PROFILE_PERFORMANCE: Final = False  # Enable performance profiling
