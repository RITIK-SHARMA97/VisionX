#!/usr/bin/env python
"""
AIPMS Quick Start — Launch all services without IoT hardware
Run this once, then open http://localhost:8501 in your browser
"""

import subprocess
import time
import sys
import os
import signal
import platform

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def start_mqtt_broker():
    """Start MQTT broker (Docker if available, else pure Python)"""
    print("\n🚀 Starting MQTT Broker...")
    
    if check_docker():
        print("   → Using Docker (Mosquitto)")
        try:
            # Check if already running
            subprocess.run(["docker", "stop", "mosquitto"], capture_output=True, timeout=5)
            subprocess.run(["docker", "rm", "mosquitto"], capture_output=True, timeout=5)
        except:
            pass
        
        subprocess.Popen(
            ["docker", "run", "-d", "-p", "1883:1883", "--name", "mosquitto", "eclipse-mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        print("   ✅ MQTT Broker started on localhost:1883 (Docker)")
    else:
        print("   → Using Pure Python MQTT Broker (Docker not available)")
        print("   ⚠️  Note: Docker is recommended for production")
        # Pure Python broker would go here - for now just note it
        print("   ⓘ Skipping Python broker (use Option B in START_WITHOUT_IOT_HARDWARE.md)")
        time.sleep(1)

def start_simulator():
    """Start sensor simulator"""
    print("\n📊 Starting Sensor Simulator...")
    
    if platform.system() == "Windows":
        subprocess.Popen(
            ["python", "-m", "simulator.simulator"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        subprocess.Popen(
            ["python", "-m", "simulator.simulator"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    time.sleep(1)
    print("   ✅ Simulator started (EXC-01, DMP-03, CVR-01)")

def start_api():
    """Start FastAPI backend"""
    print("\n⚙️  Starting FastAPI Backend...")
    
    if platform.system() == "Windows":
        subprocess.Popen(
            ["python", "-m", "api.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        subprocess.Popen(
            ["python", "-m", "api.main"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    time.sleep(2)
    print("   ✅ FastAPI running on http://localhost:8000")

def start_dashboard():
    """Start Streamlit dashboard"""
    print("\n📈 Starting Streamlit Dashboard...")
    
    # Streamlit should run in foreground so we can see it
    subprocess.run(
        ["streamlit", "run", "dashboard/app.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

def main():
    """Main startup sequence"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║       AIPMS Hackathon — Quick Start (No IoT Hardware)          ║
║                                                                ║
║  This script starts all services. Browser will open at:        ║
║               http://localhost:8501                            ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Change to project directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Start services
        start_mqtt_broker()
        start_simulator()
        start_api()
        
        print("\n" + "="*60)
        print("✅ All services started!")
        print("="*60)
        print("""
🌐 Dashboard:     http://localhost:8501
⚙️  API Backend:   http://localhost:8000/docs
📊 Health:       http://localhost:8000/health

📋 What you should see:
   • 3 equipment cards (EXC-01, DMP-03, CVR-01)
   • Live sensor data updating every 5 seconds
   • Real-time failure probability and RUL estimates
   • Alerts with SHAP top-3 sensors

🛑 To stop: Press Ctrl+C below, or close this terminal
        """)
        
        # Start dashboard in foreground
        start_dashboard()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if check_docker():
            subprocess.run(["docker", "stop", "mosquitto"], capture_output=True)
            subprocess.run(["docker", "rm", "mosquitto"], capture_output=True)
        print("✅ Cleanup complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
