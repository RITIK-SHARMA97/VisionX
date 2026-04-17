# AIPMS - Windows PowerShell Startup Script
# Phase 1: Setup & Scaffolding (2 hours)
# Runs all initialization steps: dependencies, database, MQTT, verification

Write-Host "================================"
Write-Host "AIPMS Hackathon Setup Script"
Write-Host "BIT Sindri PS-1: AI & Data Analytics"
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# === Step 1: Check Python ===
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python installed: $pythonVersion"
} else {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# === Step 2: Create virtual environment (optional) ===
Write-Host "[2/6] Setting up dependencies..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "   Creating virtual environment..."
    python -m venv .venv
    & ".\.venv\Scripts\Activate.ps1"
}

# Install requirements
Write-Host "   Installing packages from requirements.txt..."
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed"
} else {
    Write-Host "⚠️  Some dependencies failed to install, continuing..."
}

# === Step 3: Initialize Database ===
Write-Host "[3/6] Initializing SQLite database..." -ForegroundColor Yellow
$dbPath = "aipms.db"
if (Test-Path $dbPath) {
    Write-Host "   Database already exists, skipping..."
} else {
    Write-Host "   Creating database and schema..."
    sqlite3 $dbPath < config\schema.sql
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database initialized"
    } else {
        Write-Host "⚠️  Database initialization warning (may need manual setup)"
    }
}

# === Step 4: Verify imports ===
Write-Host "[4/6] Verifying Python imports..." -ForegroundColor Yellow
python -c "
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
    print(f'⚠️  Missing: {', '.join(failed)}')
    sys.exit(1)
print('✅ All imports verified')
"

# === Step 5: Test database ===
Write-Host "[5/6] Verifying database..." -ForegroundColor Yellow
$tableCount = & sqlite3 $dbPath "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
Write-Host "   Found $tableCount tables"
$equipmentCount = & sqlite3 $dbPath "SELECT COUNT(*) FROM equipment;"
Write-Host "   Found $equipmentCount equipment units"
if ($tableCount -ge 5 -and $equipmentCount -eq 3) {
    Write-Host "✅ Database verified"
} else {
    Write-Host "⚠️  Database may need manual verification"
}

# === Step 6: Completion Summary ===
Write-Host "[6/6] Phase 1 Setup Complete" -ForegroundColor Green
Write-Host ""
Write-Host "================================"
Write-Host "Next Steps:"
Write-Host "================================"
Write-Host "1. Start MQTT broker (separate terminal):"
Write-Host "   mosquitto -c config/mosquitto.conf"
Write-Host ""
Write-Host "2. Start simulator (separate terminal):"
Write-Host "   python simulator/simulator.py"
Write-Host ""
Write-Host "3. Start MQTT subscriber (separate terminal):"
Write-Host "   python simulator/mqtt_subscriber.py"
Write-Host ""
Write-Host "4. Start FastAPI backend (separate terminal):"
Write-Host "   uvicorn api.main:app --reload"
Write-Host ""
Write-Host "5. Start Streamlit dashboard (separate terminal):"
Write-Host "   streamlit run dashboard/app.py"
Write-Host ""
Write-Host "6. Run tests to verify setup:"
Write-Host "   pytest tests/test_setup.py -v"
Write-Host ""
Write-Host "Dashboard: http://localhost:8501"
Write-Host "API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
