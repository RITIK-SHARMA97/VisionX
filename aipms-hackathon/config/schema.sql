-- AIPMS SQLite Schema
-- Created: 2026-04-17
-- Auto-creates 5 core tables + indexes

CREATE TABLE IF NOT EXISTS equipment (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    location VARCHAR(100),
    status VARCHAR(10) NOT NULL DEFAULT 'normal',
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id VARCHAR(10) NOT NULL,
    timestamp DATETIME NOT NULL,
    sensor_name VARCHAR(50) NOT NULL,
    value REAL NOT NULL,
    unit VARCHAR(20),
    data_quality_flag VARCHAR(10) DEFAULT 'ok',
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    UNIQUE(equipment_id, timestamp, sensor_name)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id VARCHAR(10) NOT NULL,
    timestamp DATETIME NOT NULL,
    anomaly_score REAL CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    anomaly_label VARCHAR(10),
    failure_prob REAL CHECK (failure_prob >= 0 AND failure_prob <= 1),
    rul_hours REAL CHECK (rul_hours >= 0),
    rul_confidence_low REAL,
    rul_confidence_high REAL,
    top_features_json TEXT,
    model_version VARCHAR(20),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id VARCHAR(10) NOT NULL,
    triggered_at DATETIME NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    top_sensors TEXT,
    failure_mode_hint VARCHAR(100),
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at DATETIME,
    acknowledged_by VARCHAR(50),
    resolved_at DATETIME,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE TABLE IF NOT EXISTS maintenance_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL,
    priority_score REAL CHECK (priority_score >= 0 AND priority_score <= 1),
    priority_tier VARCHAR(10),
    failure_prob REAL,
    rul_hours REAL,
    recommended_action TEXT,
    estimated_duration_hours REAL,
    parts_required TEXT,
    scheduled_window_start DATETIME,
    scheduled_window_end DATETIME,
    status VARCHAR(20) DEFAULT 'scheduled',
    cmms_work_order_id VARCHAR(50),
    notes TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE TABLE IF NOT EXISTS model_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(50) UNIQUE NOT NULL,
    version VARCHAR(20),
    trained_at DATETIME,
    dataset VARCHAR(50),
    n_train_samples INTEGER,
    rmse REAL,
    auc_roc REAL,
    f1_score REAL,
    nasa_score REAL,
    feature_list_json TEXT,
    hyperparams_json TEXT,
    file_path VARCHAR(200)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment_time 
    ON sensor_readings(equipment_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_equipment_time 
    ON predictions(equipment_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_equipment_severity 
    ON alerts(equipment_id, severity);
CREATE INDEX IF NOT EXISTS idx_maintenance_jobs_priority 
    ON maintenance_jobs(priority_tier, scheduled_window_start);

-- Insert initial equipment (3 demo units)
INSERT OR IGNORE INTO equipment (id, name, type, location) VALUES
    ('EXC-01', 'Rope Shovel #1', 'excavator', 'North Bench'),
    ('DMP-03', 'Dumper Truck #3', 'dumper', 'Main Haul Road'),
    ('CVR-01', 'Belt Conveyor #1', 'conveyor', 'Ore Processing');
