#!/usr/bin/env python
"""Comprehensive system readiness check."""
import os
import sys
from pathlib import Path

print("=" * 70)
print("AIPMS SYSTEM READINESS CHECK")
print("=" * 70)

# 1. Check Python and dependencies
print("\n[1/5] Python Environment")
print(f"  Python version: {sys.version}")
print(f"  Working directory: {os.getcwd()}")

try:
    import streamlit
    import fastapi
    import paho.mqtt
    import sklearn
    import xgboost
    import torch
    import pandas
    import plotly
    print("  ✓ All major dependencies installed")
except ImportError as e:
    print(f"  ✗ Missing dependency: {e}")
    sys.exit(1)

# 2. Check database
print("\n[2/5] Database")
try:
    import sqlite3
    conn = sqlite3.connect("aipms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    print(f"  ✓ Database exists with {table_count} tables")
    conn.close()
except Exception as e:
    print(f"  ✗ Database error: {e}")
    sys.exit(1)

# 3. Check ML models
print("\n[3/5] ML Models")
models_dir = Path("models/saved")
if models_dir.exists():
    models = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.pt"))
    print(f"  ✓ Found {len(models)} trained models:")
    for m in models:
        size_kb = m.stat().st_size / 1024
        print(f"    - {m.name} ({size_kb:.1f} KB)")
else:
    print("  ✗ Models directory not found")
    sys.exit(1)

# 4. Check imports
print("\n[4/5] Core Imports")
try:
    from simulator import SensorSimulator, SimulatorEngine, MQTTSubscriber
    from api.main import app as fastapi_app
    from api.orm import Base, Equipment
    from api.schema import MaintenanceAlert
    from dashboard.app import create_dashboard
    print("  ✓ All core modules import successfully")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

# 5. Check configuration
print("\n[5/5] Configuration")
try:
    import config_constants as cfg
    print(f"  ✓ Config loaded:")
    print(f"    - Simulator: {cfg.NUM_EQUIPMENT} units")
    print(f"    - API host: {cfg.API_HOST}:{cfg.API_PORT}")
    print(f"    - MQTT broker: {cfg.MQTT_HOST}:{cfg.MQTT_PORT}")
except Exception as e:
    print(f"  ✗ Config error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ ALL SYSTEMS READY")
print("=" * 70)
