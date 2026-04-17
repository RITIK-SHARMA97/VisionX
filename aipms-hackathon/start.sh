#!/bin/bash
# AIPMS - Linux/macOS Startup Script
# Phase 1: Setup & Scaffolding (2 hours)
# Runs all initialization steps: dependencies, database, MQTT, verification

echo "================================"
echo "AIPMS Hackathon Setup Script"
echo "BIT Sindri PS-1: AI & Data Analytics"
echo "================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# === Step 1: Check Python ===
echo "[1/6] Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python installed: $PYTHON_VERSION"
else
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

# === Step 2: Create virtual environment (optional) ===
echo "[2/6] Setting up dependencies..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

source venv/bin/activate

echo "   Installing packages from requirements.txt..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "⚠️  Some dependencies failed to install, continuing..."
fi

# === Step 3: Initialize Database ===
echo "[3/6] Initializing SQLite database..."
if [ -f "aipms.db" ]; then
    echo "   Database already exists, skipping..."
else
    echo "   Creating database and schema..."
    sqlite3 aipms.db < config/schema.sql
    if [ $? -eq 0 ]; then
        echo "✅ Database initialized"
    else
        echo "⚠️  Database initialization warning (may need manual setup)"
    fi
fi

# === Step 4: Verify imports ===
echo "[4/6] Verifying Python imports..."
python3 << 'PYTHON_CHECK'
import sys
packages = ['pandas', 'numpy', 'sqlalchemy', 'paho.mqtt', 'fastapi', 'streamlit']
failed = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✓ {pkg}')
    except ImportError:
        failed.append(pkg)
        print(f'  ✗ {pkg}')

if failed:
    print(f'⚠️  Missing: {", ".join(failed)}')
    sys.exit(1)
print('✅ All imports verified')
PYTHON_CHECK

# === Step 5: Test database ===
echo "[5/6] Verifying database..."
TABLE_COUNT=$(sqlite3 aipms.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
echo "   Found $TABLE_COUNT tables"
EQUIPMENT_COUNT=$(sqlite3 aipms.db "SELECT COUNT(*) FROM equipment;")
echo "   Found $EQUIPMENT_COUNT equipment units"
if [ "$TABLE_COUNT" -ge 5 ] && [ "$EQUIPMENT_COUNT" -eq 3 ]; then
    echo "✅ Database verified"
else
    echo "⚠️  Database may need manual verification"
fi

# === Step 6: Completion Summary ===
echo "[6/6] Phase 1 Setup Complete"
echo ""
echo "================================"
echo "Next Steps:"
echo "================================"
echo "1. Start MQTT broker (separate terminal):"
echo "   mosquitto -c config/mosquitto.conf"
echo ""
echo "2. Start simulator (separate terminal):"
echo "   python3 simulator/simulator.py"
echo ""
echo "3. Start MQTT subscriber (separate terminal):"
echo "   python3 simulator/mqtt_subscriber.py"
echo ""
echo "4. Start FastAPI backend (separate terminal):"
echo "   uvicorn api.main:app --reload"
echo ""
echo "5. Start Streamlit dashboard (separate terminal):"
echo "   streamlit run dashboard/app.py"
echo ""
echo "6. Run tests to verify setup:"
echo "   pytest tests/test_setup.py -v"
echo ""
echo "Dashboard: http://localhost:8501"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "================================"
