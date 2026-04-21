# AIPMS Dashboard Demo Runner
# This script starts the dashboard for demonstration

Write-Host "╔════════════════════════════════════════════════════════════╗"
Write-Host "║     AIPMS - AI Predictive Maintenance Dashboard Demo      ║"
Write-Host "║                    Project Status: ✅ READY                ║"
Write-Host "╚════════════════════════════════════════════════════════════╝"
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python found" -ForegroundColor Green
Write-Host ""

# Check Streamlit
Write-Host "Checking Streamlit installation..." -ForegroundColor Yellow
python -c "import streamlit; print(f'Streamlit version: {streamlit.__version__}')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Streamlit not found. Installing..." -ForegroundColor Red
    pip install streamlit --quiet
}
Write-Host "✅ Streamlit ready" -ForegroundColor Green
Write-Host ""

# Display demo information
Write-Host "╔════════════════════════════════════════════════════════════╗"
Write-Host "║                    DEMO FEATURES                          ║"
Write-Host "╠════════════════════════════════════════════════════════════╣"
Write-Host "║ ✓ 4 Interactive Dashboard Pages                           ║"
Write-Host "║   • Fleet Overview - Equipment status & KPIs              ║"
Write-Host "║   • Equipment Detail - Sensor trends & RUL degradation   ║"
Write-Host "║   • Alert Feed - Real-time failure predictions           ║"
Write-Host "║   • Maintenance Schedule - Gantt timeline visualization   ║"
Write-Host "║                                                           ║"
Write-Host "║ ✓ ML Models Integrated                                    ║"
Write-Host "║   • Anomaly Detection (Isolation Forest)                 ║"
Write-Host "║   • Failure Prediction (XGBoost)                         ║"
Write-Host "║   • RUL Estimation (LSTM)                                ║"
Write-Host "║                                                           ║"
Write-Host "║ ✓ Data Source: NASA C-MAPSS Dataset                      ║"
Write-Host "║   Sample data demonstrates full UI/UX capabilities       ║"
Write-Host "╚════════════════════════════════════════════════════════════╝"
Write-Host ""

# Start dashboard
Write-Host "🚀 Starting Streamlit Dashboard..." -ForegroundColor Green
Write-Host "📱 Dashboard will open at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

cd (Split-Path -Parent $MyInvocation.MyCommand.Path)
python -m streamlit run dashboard/app.py --logger.level=warning
