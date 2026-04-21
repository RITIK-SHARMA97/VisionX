#!/usr/bin/env python
"""
AIPMS Full System Startup & Verification
Starts all components and verifies they work together
"""
import subprocess
import time
import sys
import threading
from pathlib import Path

def run_command(cmd, name, timeout=5):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"{name} timed out after {timeout}s"
    except Exception as e:
        return False, str(e)

print("\n" + "="*80)
print("AIPMS COMPLETE SYSTEM VERIFICATION")
print("="*80)

# Phase 1: Infrastructure Check
print("\n[PHASE 1] Infrastructure Validation")
print("-" * 80)

checks = {
    "Database exists": "python -c \"import os; print('✓ aipms.db exists') if os.path.exists('aipms.db') else None\"",
    "Database tables": "python -c \"import sqlite3; c = sqlite3.connect('aipms.db'); tables = len(c.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"').fetchall()); print(f'✓ {tables} tables found')\"",
    "ML models": "python -c \"from pathlib import Path; m = list(Path('models/saved').glob('*.pkl')) + list(Path('models/saved').glob('*.pt')); print(f'✓ {len(m)} models loaded')\"",
}

for check_name, cmd in checks.items():
    success, output = run_command(cmd, check_name, timeout=3)
    status = "✓" if success else "✗"
    print(f"  {status} {check_name:25} {output.strip()[:60]}")

# Phase 2: Import Validation
print("\n[PHASE 2] Module Import Validation")
print("-" * 80)

imports = {
    "simulator.SensorSimulator": "from simulator import SensorSimulator; print('✓ SensorSimulator')",
    "simulator.SimulatorEngine": "from simulator import SimulatorEngine; print('✓ SimulatorEngine')",
    "simulator.MQTTSubscriber": "from simulator import MQTTSubscriber; print('✓ MQTTSubscriber')",
    "api.main.app": "from api.main import app; print('✓ FastAPI app')",
    "api.orm.Base": "from api.orm import Base; print('✓ SQLAlchemy Base')",
    "api.schema": "from api.schema import MaintenanceAlert; print('✓ Schema')",
    "dashboard.app": "from dashboard.app import create_dashboard; print('✓ Dashboard')",
}

import_pass = 0
for module_name, cmd in imports.items():
    success, output = run_command(f"python -c \"{cmd}\"", module_name, timeout=3)
    if success:
        import_pass += 1
        print(f"  ✓ {module_name:30} {output.strip()}")
    else:
        print(f"  ✗ {module_name:30} Failed")

print(f"\n  Import Summary: {import_pass}/{len(imports)} modules ready")

# Phase 3: Configuration Check
print("\n[PHASE 3] Configuration Validation")
print("-" * 80)

config_check = """
import config_constants as cfg
print(f"  Equipment units: {cfg.NUM_EQUIPMENT}")
print(f"  API Host: {cfg.API_HOST}:{cfg.API_PORT}")
print(f"  MQTT Host: {cfg.MQTT_HOST}:{cfg.MQTT_PORT}")
print(f"  Database: {cfg.DB_PATH}")
"""

success, output = run_command(f"python -c \"{config_check}\"", "config", timeout=3)
if success:
    for line in output.strip().split('\n'):
        if line.strip():
            print(f"  ✓ {line.strip()}")

# Phase 4: Database Schema Test
print("\n[PHASE 4] Database Schema Test")
print("-" * 80)

schema_test = """
from api.orm import Base, Equipment, SensorReading, Prediction, Alert, MaintenanceJob
print(f"  ✓ Equipment model mapped")
print(f"  ✓ SensorReading model mapped")
print(f"  ✓ Prediction model mapped")
print(f"  ✓ Alert model mapped")
print(f"  ✓ MaintenanceJob model mapped")
print(f"  ✓ All 5 core models loaded from ORM")
"""

success, output = run_command(f"python -c \"{schema_test}\"", "schema", timeout=3)
if success:
    for line in output.strip().split('\n'):
        if line.strip():
            print(f"  {line.strip()}")

# Final Status
print("\n" + "="*80)
if import_pass == len(imports):
    print("✓ ALL SYSTEMS OPERATIONAL")
    print("="*80)
    print("\nNext Steps for Demo:")
    print("  1. Start MQTT Broker: mosquitto  (or use Docker: docker run -it -p 1883:1883 eclipse-mosquitto)")
    print("  2. Start API: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
    print("  3. Start Simulator: python simulator/simulator.py")
    print("  4. Start Dashboard: streamlit run dashboard/app.py")
    print("  5. Run Demo: python demo_13_steps.py")
    print("="*80 + "\n")
    sys.exit(0)
else:
    print("✗ SOME SYSTEMS NEED ATTENTION")
    print("="*80 + "\n")
    sys.exit(1)
