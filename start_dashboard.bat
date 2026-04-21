@echo off
REM AIPMS Dashboard Launcher - Windows
REM This script starts the Streamlit dashboard on localhost:8501

echo ================================
echo AIPMS Dashboard Launcher
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and add it to PATH
    exit /b 1
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit is not installed
    echo Run: pip install streamlit
    exit /b 1
)

REM Navigate to project directory
cd /d "%~dp0\aipms-hackathon"
if errorlevel 1 (
    echo ERROR: Failed to navigate to aipms-hackathon directory
    exit /b 1
)

REM Check if dashboard/app.py exists
if not exist "dashboard\app.py" (
    echo ERROR: dashboard/app.py not found
    echo Make sure you're running this from the BIT-SINDRI directory
    exit /b 1
)

echo.
echo ✅ Prerequisites check passed
echo.
echo Launching dashboard on http://localhost:8501
echo.
echo NOTE: Make sure FastAPI backend is running on port 8000:
echo   python api/main.py
echo.
echo Press Ctrl+C to stop the dashboard
echo.

REM Launch streamlit
streamlit run dashboard/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Dashboard failed to start
    echo Check that all dependencies are installed: pip install -r requirements.txt
    exit /b 1
)
