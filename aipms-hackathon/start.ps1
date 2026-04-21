# AIPMS Service Launcher - Phase 6: Integration & Full Flow Testing
# Launches all 5 services in coordinated sequence
# Usage: .\start.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    🚀 AIPMS SERVICE LAUNCHER (Phase 6)                         ║" -ForegroundColor Cyan
Write-Host "║         Launching 5 services: MQTT → Simulator → API → Dashboard              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"
$PID_FILE = Join-Path $LOG_DIR "service_pids.txt"

if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }
"" | Out-File -FilePath $PID_FILE -Force

Push-Location $PROJECT_ROOT

# ─────────────────────────────────────────────────────────────────────────────────
# SERVICE CONFIGURATIONS
# ─────────────────────────────────────────────────────────────────────────────────

$SERVICES = @(
    @{
        Name = "Mosquitto MQTT Broker"
        Command = "docker"
        Args = @("run", "-d", "-p", "1883:1883", "--name", "aipms-mosquitto", "eclipse-mosquitto:latest")
        Port = 1883
        Timeout = 10
        IsMockable = $true
    },
    @{
        Name = "MQTT Subscriber"
        Command = "python"
        Args = @("-m", "simulator.mqtt_subscriber")
        Port = $null
        Timeout = 8
        IsMockable = $false
    },
    @{
        Name = "Sensor Simulator"
        Command = "python"
        Args = @("-m", "simulator.simulator")
        Port = $null
        Timeout = 8
        IsMockable = $false
    },
    @{
        Name = "FastAPI Backend"
        Command = "python"
        Args = @("-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000")
        Port = 8000
        Timeout = 15
        IsMockable = $false
    },
    @{
        Name = "Streamlit Dashboard"
        Command = "streamlit"
        Args = @("run", "dashboard/app.py", "--server.port", "8501", "--server.headless", "true", "--logger.level=error")
        Port = 8501
        Timeout = 15
        IsMockable = $false
    }
)

# ─────────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────────

function Test-PortAvailable {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.ConnectAsync("127.0.0.1", $Port).Wait(100)
        $connection.Close()
        return $false
    } catch { return $true }
}

function Wait-ServiceReady {
    param([hashtable]$Service)
    
    $name = $Service.Name
    $port = $Service.Port
    $timeout = $Service.Timeout
    $startTime = Get-Date
    
    Write-Host "   ⏳ Waiting for service to be ready (max ${timeout}s)..." -ForegroundColor Yellow
    
    while ((Get-Date) -lt $startTime.AddSeconds($timeout)) {
        if ($null -eq $port) {
            Start-Sleep -Milliseconds 500
            Write-Host "   ✅ Service started" -ForegroundColor Green
            return $true
        }
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port" -ErrorAction SilentlyContinue -TimeoutSec 1
            Write-Host "   ✅ Service responding on port $port" -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    
    Write-Host "   ⚠️  Timeout waiting for service - may still be starting..." -ForegroundColor Yellow
    return $false
}

function Start-Service {
    param([hashtable]$Service, [int]$Index)
    
    $name = $Service.Name
    $command = $Service.Command
    $args = $Service.Args
    $port = $Service.Port
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "[$Index/$($SERVICES.Count)] Launching: $name" -ForegroundColor Cyan
    
    if ($null -ne $port) {
        if (-not (Test-PortAvailable -Port $port)) {
            Write-Host "   ❌ Port $port is already in use!" -ForegroundColor Red
            return $false
        }
    }
    
    try {
        $logFile = Join-Path $LOG_DIR "$($name -replace ' ', '_').log"
        $process = Start-Process -FilePath $command -ArgumentList $args -WorkingDirectory $PROJECT_ROOT `
                                 -RedirectStandardOutput $logFile -RedirectStandardError $logFile `
                                 -PassThru -NoNewWindow
        
        Write-Host "   ✅ Process started (PID: $($process.Id))" -ForegroundColor Green
        Add-Content -Path $PID_FILE -Value "$($process.Id)"
        
        Start-Sleep -Milliseconds 1500
        Wait-ServiceReady -Service $Service | Out-Null
        return $true
    } catch {
        Write-Host "   ❌ Failed: $_" -ForegroundColor Red
        return $false
    }
}

function Stop-AllServices {
    Write-Host "`n🛑 Stopping all services..." -ForegroundColor Yellow
    
    docker stop aipms-mosquitto 2>&1 | Out-Null
    docker rm aipms-mosquitto 2>&1 | Out-Null
    
    if (Test-Path $PID_FILE) {
        $pids = Get-Content $PID_FILE
        foreach ($pid in $pids) {
            Stop-Process -Id $pid -ErrorAction SilentlyContinue -Force
        }
    }
    
    Write-Host "   ✅ All services stopped" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────────

$success = 0
foreach ($service in $SERVICES) {
    if (Start-Service -Service $service -Index ($success + 1)) {
        $success++
    }
}

Write-Host ""
if ($success -eq $SERVICES.Count) {
    Write-Host "╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                   ✅ ALL SERVICES RUNNING SUCCESSFULLY                        ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access Points:" -ForegroundColor Cyan
    Write-Host "   Dashboard  : http://localhost:8501" -ForegroundColor White
    Write-Host "   API Docs   : http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   API Health : http://localhost:8000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Service Logs:" -ForegroundColor Cyan
    Write-Host "   Location: $LOG_DIR" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⏳ Running... Press Ctrl+C to stop all services" -ForegroundColor Yellow
    
    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Stop-AllServices }
    
    try {
        while ($true) { Start-Sleep -Seconds 60 }
    } finally {
        Stop-AllServices
        Pop-Location
    }
} else {
    Write-Host "❌ Failed to start all services ($success/$($SERVICES.Count) started)" -ForegroundColor Red
    Stop-AllServices
    Pop-Location
    exit 1
}
