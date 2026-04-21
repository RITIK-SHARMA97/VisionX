# AIPMS Quick Start for Windows PowerShell
# No IoT hardware needed — uses simulated sensor data
# Run this script to start all services

param(
    [switch]$NoDocker = $false
)

function Write-Header {
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       AIPMS Hackathon — Quick Start (No IoT Hardware)          ║" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "║  Services will start. Open browser at:                         ║" -ForegroundColor Cyan
    Write-Host "║               http://localhost:8501                            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Check-Docker {
    try {
        $result = docker ps 2>$null
        return $?
    } catch {
        return $false
    }
}

function Start-MQTTBroker {
    Write-Host "`n🚀 Starting MQTT Broker..." -ForegroundColor Green
    
    if ((Check-Docker) -and -not $NoDocker) {
        Write-Host "   → Using Docker (Mosquitto)" -ForegroundColor White
        
        # Clean up any existing container
        docker stop mosquitto 2>$null | Out-Null
        docker rm mosquitto 2>$null | Out-Null
        
        # Start new container
        docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "   ✅ MQTT Broker started on localhost:1883 (Docker)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Docker not available or --NoDocker flag set" -ForegroundColor Yellow
        Write-Host "   ℹ️  For pure Python MQTT broker, see START_WITHOUT_IOT_HARDWARE.md" -ForegroundColor White
    }
}

function Start-Simulator {
    Write-Host "`n📊 Starting Sensor Simulator..." -ForegroundColor Green
    Start-Process -FilePath python -ArgumentList "-m", "simulator.simulator" -NoNewWindow
    Start-Sleep -Seconds 1
    Write-Host "   ✅ Simulator started (EXC-01, DMP-03, CVR-01)" -ForegroundColor Green
}

function Start-API {
    Write-Host "`n⚙️  Starting FastAPI Backend..." -ForegroundColor Green
    Start-Process -FilePath python -ArgumentList "-m", "api.main" -NoNewWindow
    Start-Sleep -Seconds 2
    Write-Host "   ✅ FastAPI running on http://localhost:8000" -ForegroundColor Green
}

function Start-Dashboard {
    Write-Host "`n📈 Starting Streamlit Dashboard..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    
    Write-Host "`n" -ForegroundColor White
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "✅ All services started!" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "`n🌐 Dashboard:     http://localhost:8501" -ForegroundColor Cyan
    Write-Host "⚙️  API Backend:   http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "📊 Health:       http://localhost:8000/health" -ForegroundColor Cyan
    
    Write-Host "`n📋 What you should see:" -ForegroundColor White
    Write-Host "   • 3 equipment cards (EXC-01, DMP-03, CVR-01)" -ForegroundColor Gray
    Write-Host "   • Live sensor data updating every 5 seconds" -ForegroundColor Gray
    Write-Host "   • Real-time failure probability and RUL estimates" -ForegroundColor Gray
    Write-Host "   • Alerts with SHAP top-3 sensors" -ForegroundColor Gray
    Write-Host "   • Maintenance schedule with priority ranking" -ForegroundColor Gray
    
    Write-Host "`n🛑 To stop: Close this window or press Ctrl+C in Streamlit" -ForegroundColor Yellow
    Write-Host "`n" -ForegroundColor White
    
    # Start Streamlit (this will stay in foreground)
    streamlit run dashboard/app.py
}

function Cleanup {
    Write-Host "`n🛑 Shutting down..." -ForegroundColor Yellow
    
    # Stop Docker if it was started
    if ((Check-Docker) -and -not $NoDocker) {
        docker stop mosquitto 2>$null | Out-Null
        docker rm mosquitto 2>$null | Out-Null
    }
    
    # Kill Python processes
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Main execution
try {
    Write-Header
    
    # Navigate to project directory
    $projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    Push-Location $projectRoot
    
    # Start all services
    Start-MQTTBroker
    Start-Simulator
    Start-API
    Start-Dashboard
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}
finally {
    Cleanup
    Pop-Location
}
