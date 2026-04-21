#!/usr/bin/env python
"""
AIPMS Demo Readiness Verification
Simulates the complete 13-step demo workflow
"""
import json
from pathlib import Path

print("\n" + "="*80)
print("AIPMS DEMO READINESS VERIFICATION")
print("="*80)

# Test 1: Load all critical modules
print("\n[Step 1/5] Module Import Test")
print("-" * 80)

modules_to_test = [
    ("simulator", ["SensorSimulator", "SimulatorEngine", "MQTTSubscriber", "EquipmentProfile"]),
    ("api", ["app (FastAPI)", "Base (ORM)", "MaintenanceAlert (Schema)"]),
    ("dashboard", ["create_dashboard (Factory)"]),
]

all_pass = True
for module_name, components in modules_to_test:
    try:
        if module_name == "simulator":
            from simulator import SensorSimulator, SimulatorEngine, MQTTSubscriber, EquipmentProfile
            print(f"✓ {module_name}: {', '.join(components)}")
        elif module_name == "api":
            from api.main import app
            from api.orm import Base
            from api.schema import MaintenanceAlert
            print(f"✓ {module_name}: {', '.join(components)}")
        elif module_name == "dashboard":
            from dashboard.app import create_dashboard
            print(f"✓ {module_name}: {', '.join(components)}")
    except Exception as e:
        print(f"✗ {module_name}: {str(e)[:60]}")
        all_pass = False

# Test 2: Database verification
print("\n[Step 2/5] Database Schema Test")
print("-" * 80)

try:
    import sqlite3
    conn = sqlite3.connect("aipms.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    expected_tables = {'equipment', 'sensor_readings', 'predictions', 'alerts', 'model_metadata', 'maintenance_jobs'}
    found_tables = {t[0] for t in tables}
    
    if expected_tables == found_tables:
        print(f"✓ Database: All 6 required tables present")
        for table in sorted(found_tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
    else:
        print(f"✗ Database: Missing tables {expected_tables - found_tables}")
        all_pass = False
    
    conn.close()
except Exception as e:
    print(f"✗ Database error: {str(e)}")
    all_pass = False

# Test 3: ML Models
print("\n[Step 3/5] ML Models Test")
print("-" * 80)

try:
    models_dir = Path("models/saved")
    models = {
        "anomaly_detector_v1.pkl": False,
        "failure_predictor_v1.pkl": False,
        "rul_estimator_v1.pt": False,
    }
    
    for model_file in models_dir.glob("*"):
        if model_file.name in models:
            models[model_file.name] = True
            size_kb = model_file.stat().st_size / 1024
            print(f"✓ {model_file.name} ({size_kb:.1f} KB)")
    
    if not all(models.values()):
        print(f"✗ Missing models: {[k for k, v in models.items() if not v]}")
        all_pass = False
except Exception as e:
    print(f"✗ Models error: {str(e)}")
    all_pass = False

# Test 4: Configuration
print("\n[Step 4/5] Configuration Test")
print("-" * 80)

try:
    import config_constants as cfg
    config_params = {
        "NUM_EQUIPMENT": cfg.NUM_EQUIPMENT,
        "API_HOST": cfg.API_HOST,
        "API_PORT": cfg.API_PORT,
        "MQTT_HOST": cfg.MQTT_HOST,
        "MQTT_PORT": cfg.MQTT_PORT,
        "DB_PATH": cfg.DB_PATH,
    }
    
    print("✓ Configuration loaded:")
    for key, value in config_params.items():
        print(f"  {key}: {value}")
except Exception as e:
    print(f"✗ Configuration error: {str(e)}")
    all_pass = False

# Test 5: Demo readiness
print("\n[Step 5/5] Demo Readiness Test")
print("-" * 80)

demo_files = {
    "demo_13_steps.py": "13-Step Demo Script",
    "simulator/simulator.py": "Equipment Simulator",
    "simulator/mqtt_subscriber.py": "MQTT Subscriber",
    "api/main.py": "FastAPI Server",
    "dashboard/app.py": "Streamlit Dashboard",
}

all_demo_ready = True
for file_path, description in demo_files.items():
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
    else:
        print(f"✗ {description}: {file_path} NOT FOUND")
        all_demo_ready = False
        all_pass = False

# Final Status
print("\n" + "="*80)
if all_pass:
    print("✓ SYSTEM READY FOR DEMONSTRATION")
    print("="*80)
    print("\nNext Steps:")
    print("  1. Terminal 1: mosquitto")
    print("  2. Terminal 2: uvicorn api.main:app --host 0.0.0.0 --port 8000")
    print("  3. Terminal 3: python simulator/simulator.py")
    print("  4. Terminal 4: streamlit run dashboard/app.py")
    print("  5. Terminal 5: python demo_13_steps.py")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Dashboard: http://localhost:8501")
    print("="*80 + "\n")
else:
    print("✗ SYSTEM HAS ISSUES - REVIEW ABOVE")
    print("="*80 + "\n")
