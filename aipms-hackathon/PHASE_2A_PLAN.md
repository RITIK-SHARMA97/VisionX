# Phase 2A Implementation Plan: Data Integration & IoT Pipeline

**Duration:** 3 hours  
**Owner:** Backend Dev  
**Parallel with:** Phase 2B (ML Data Preparation)  
**Status:** Ready for Execution

---

## Overview

Set up end-to-end IoT data flow:
- **MQTT Broker** (Mosquitto) on port 1883
- **Sensor Simulator** publishing realistic sensor streams from 3 equipment units at different degradation stages
- **MQTT Subscriber** consuming, validating, and storing to SQLite with data quality flags
- **Database** populated with time-series sensor readings and anomaly markers

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  SensorSimulator (simulator.py)                      │
│  ├─ EXC-01: accelerated_degradation (fails in 3m)   │
│  ├─ DMP-03: early_degradation (warning state)       │
│  └─ CVR-01: healthy (normal)                        │
└─────────────┬───────────────────────────────────────┘
              │ MQTT publish (1 msg/sec each)
              ↓
      ┌──────────────────┐
      │  Mosquitto       │
      │  Port: 1883      │
      └────────┬─────────┘
               │ mines/equipment/{id}/sensors
               ↓
   ┌───────────────────────────┐
   │  MQTTSubscriber           │
   │  ├─ JSON validation       │
   │  ├─ Range checking        │
   │  ├─ Quality flagging      │
   │  └─ SQLite writer         │
   └───────────────┬───────────┘
                   ↓
         ┌──────────────────┐
         │  SQLite Database │
         ├─ equipment      │
         ├─ sensor_readings│
         └─ quality_flags  │
         └──────────────────┘
```

---

## Phase 2A-1: MQTT Broker Setup (15 minutes)

### Step 1.1: Mosquitto Configuration

Create `config/mosquitto.conf`:

```conf
# Mosquitto Configuration for AIPMS
listener 1883
protocol mqtt

# Persistence
persistence true
persistence_location ./mosquitto_data/

# Logging
log_dest file ./mosquitto_data/mosquitto.log
log_dest stdout
log_type all
log_timestamp true

# Security (disabled for prototype)
allow_anonymous true

# Limits
max_connections 100
max_inflight_messages 20
message_size_limit 0
```

**Verification:**
```powershell
# Check config
Get-Content config/mosquitto.conf | Select-String "listener"
```

---

### Step 1.2: Start Mosquitto (Docker)

```powershell
# Create data directory
mkdir -p mosquitto_data

# Start container
docker run -d `
  --name aipms-mosquitto `
  -p 1883:1883 `
  -v "$pwd/config/mosquitto.conf:/mosquitto/config/mosquitto.conf" `
  -v "$pwd/mosquitto_data:/mosquitto/data" `
  eclipse-mosquitto:2.0

# Verify
docker ps | findstr aipms-mosquitto
```

---

## Phase 2A-2: Sensor Simulator (50 minutes)

### Step 2.1: Create EquipmentProfile & SensorSimulator Classes

Create `simulator/equipment_profiles.py`:

```python
import math
import random
from datetime import datetime
from dataclasses import dataclass
from typing import Dict

@dataclass
class SensorReading:
    equipment_id: str
    timestamp: str
    sensor_name: str
    value: float
    unit: str

class EquipmentProfile:
    """Simulates equipment with lifecycle-based degradation."""
    
    def __init__(self, equipment_id: str, lifecycle_stage: str):
        self.equipment_id = equipment_id
        self.lifecycle_stage = lifecycle_stage
        
        # Lifecycle progress mapping
        self.progress = {
            'healthy': 0.3,
            'early_degradation': 0.7,
            'accelerated_degradation': 0.90,
            'imminent_failure': 0.99
        }[lifecycle_stage]
        
        # Sensor baselines (mining equipment specs)
        self.baselines = {
            'temperature_C': 75.0,
            'vibration_mm_s': 1.2,
            'hydraulic_pressure_bar': 200.0,
            'rpm': 1400.0,
            'fuel_consumption_L_hr': 20.0,
        }
    
    def get_sensor_value(self, sensor_name: str) -> float:
        """Generate degradation-aware sensor value."""
        base = self.baselines[sensor_name]
        noise = random.gauss(0, base * 0.02)  # 2% Gaussian noise
        
        # Lifecycle multiplier
        mult = self._get_multiplier(sensor_name)
        value = base * mult + noise
        
        return max(0.0, value)
    
    def _get_multiplier(self, sensor_name: str) -> float:
        """Lifecycle degradation multiplier."""
        progress = self.progress
        
        if self.lifecycle_stage == 'healthy':
            return 1.0 + random.gauss(0, 0.01)
        
        elif self.lifecycle_stage == 'early_degradation':
            drift = progress * 0.05  # +5% over lifecycle
            return 1.0 + drift + random.gauss(0, 0.02)
        
        elif self.lifecycle_stage == 'accelerated_degradation':
            # Exponential rise + spike events
            drift = math.exp((progress - 0.7) * 5) * 0.20
            spike = 0.1 if random.random() < 0.15 else 0
            return 1.0 + drift + spike + random.gauss(0, 0.03)
        
        elif self.lifecycle_stage == 'imminent_failure':
            # Extreme values + frequent anomalies
            if random.random() < 0.3:
                return random.uniform(0.0, 0.3)  # Near-failure
            return 2.0 + random.gauss(0, 0.5)  # Wild swings
        
        return 1.0
    
    def generate_readings(self) -> list:
        """Generate readings for all sensors."""
        readings = []
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        for sensor, base in self.baselines.items():
            value = self.get_sensor_value(sensor)
            unit = self._get_unit(sensor)
            
            readings.append(SensorReading(
                equipment_id=self.equipment_id,
                timestamp=timestamp,
                sensor_name=sensor,
                value=value,
                unit=unit
            ))
        
        return readings
    
    @staticmethod
    def _get_unit(sensor_name: str) -> str:
        units = {
            'temperature_C': '°C',
            'vibration_mm_s': 'mm/s',
            'hydraulic_pressure_bar': 'bar',
            'rpm': 'RPM',
            'fuel_consumption_L_hr': 'L/hr',
        }
        return units.get(sensor_name, '?')
```

Create `simulator/simulator.py`:

```python
import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime
from equipment_profiles import EquipmentProfile

class SensorSimulator:
    """Publishes sensor readings from multiple equipment units to MQTT."""
    
    def __init__(self, equipment_id: str, lifecycle_stage: str, 
                 broker_host: str = "localhost", broker_port: int = 1883):
        self.equipment_id = equipment_id
        self.profile = EquipmentProfile(equipment_id, lifecycle_stage)
        self.client = mqtt.Client(client_id=f"sim-{equipment_id}")
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.running = False
        
        # Set MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ {self.equipment_id} connected to MQTT broker")
            self.running = True
        else:
            print(f"❌ {self.equipment_id} MQTT connection failed: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"⚠️ {self.equipment_id} disconnected from MQTT: {rc}")
        self.running = False
    
    def start(self):
        """Connect and start publishing."""
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
    
    def publish_loop(self, hz: float = 1.0):
        """Publish readings at specified frequency (Hz)."""
        interval = 1.0 / hz
        
        while True:
            try:
                if self.running:
                    readings = self.profile.generate_readings()
                    
                    # Publish each sensor reading
                    for reading in readings:
                        payload = {
                            'equipment_id': reading.equipment_id,
                            'timestamp': reading.timestamp,
                            'sensor_name': reading.sensor_name,
                            'value': float(reading.value),
                            'unit': reading.unit
                        }
                        
                        topic = f"mines/equipment/{self.equipment_id}/sensors"
                        self.client.publish(topic, json.dumps(payload), qos=1)
                
                time.sleep(interval)
            
            except Exception as e:
                print(f"❌ {self.equipment_id} publish error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Gracefully shutdown."""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

def main():
    """Run 3 equipment simulators at different lifecycle stages."""
    
    print("🚀 Starting AIPMS Sensor Simulator...")
    
    # Define equipment with different degradation stages
    equipment = [
        ("EXC-01", "accelerated_degradation"),  # Will trigger alerts in ~3 min
        ("DMP-03", "early_degradation"),         # Warning state
        ("CVR-01", "healthy"),                   # Normal
    ]
    
    simulators = []
    
    # Start all simulators
    for eq_id, stage in equipment:
        sim = SensorSimulator(eq_id, stage)
        sim.start()
        
        # Start publish loop in background thread
        t = threading.Thread(target=sim.publish_loop, args=(1.0,), daemon=True)
        t.start()
        
        simulators.append(sim)
        print(f"✅ {eq_id} simulator started ({stage})")
        time.sleep(0.5)  # Stagger starts
    
    print("\n📡 Simulators running. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down simulators...")
        for sim in simulators:
            sim.stop()
        print("✅ All simulators stopped")

if __name__ == "__main__":
    main()
```

**Verification:**
```powershell
# Test imports
python -c "from simulator.simulator import SensorSimulator; print('✅ Imports OK')"

# Start simulator in background
Start-Process powershell -ArgumentList "cd aipms-hackathon; python simulator/simulator.py"

# Verify MQTT messages (in another terminal)
mosquitto_sub -h localhost -p 1883 -t "mines/equipment/+/sensors" -C 5
```

---

## Phase 2A-3: MQTT Subscriber (40 minutes)

### Step 3.1: Create MQTTSubscriber Class

Create `simulator/mqtt_subscriber.py`:

```python
import paho.mqtt.client as mqtt
import json
import sqlite3
from datetime import datetime
from pathlib import Path

class MQTTSubscriber:
    """Consumes MQTT messages, validates, stores to SQLite."""
    
    def __init__(self, db_path: str = "aipms.db", 
                 broker_host: str = "localhost", broker_port: int = 1883):
        self.db_path = db_path
        self.client = mqtt.Client(client_id="subscriber-aipms")
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Sensor thresholds for quality flagging
        self.thresholds = {
            'temperature_C': (40, 120),
            'vibration_mm_s': (0, 10),
            'hydraulic_pressure_bar': (100, 300),
            'rpm': (600, 2500),
            'fuel_consumption_L_hr': (5, 50),
        }
        
        # Stats tracking
        self.messages_received = 0
        self.rows_inserted = 0
        self.errors = 0
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Subscriber connected to MQTT broker")
            client.subscribe("mines/equipment/+/sensors", qos=1)
            print("📡 Subscribed to mines/equipment/+/sensors")
        else:
            print(f"❌ MQTT connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        self.messages_received += 1
        
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            equipment_id = payload.get('equipment_id')
            timestamp = payload.get('timestamp')
            sensor_name = payload.get('sensor_name')
            value = float(payload.get('value', 0))
            unit = payload.get('unit', '?')
            
            # Data quality check
            quality_flag = self._check_quality(sensor_name, value)
            
            # Write to database
            self._insert_reading(
                equipment_id=equipment_id,
                timestamp=timestamp,
                sensor_name=sensor_name,
                value=value,
                unit=unit,
                quality_flag=quality_flag
            )
            
            # Log quality issues
            if quality_flag != 'ok':
                print(f"⚠️  {equipment_id}/{sensor_name}: {quality_flag} ({value} {unit})")
        
        except Exception as e:
            self.errors += 1
            print(f"❌ Error processing message: {e}")
    
    def _check_quality(self, sensor_name: str, value: float) -> str:
        """Check if sensor value is within normal range."""
        if sensor_name not in self.thresholds:
            return 'ok'
        
        min_val, max_val = self.thresholds[sensor_name]
        
        if value < min_val or value > max_val:
            return 'suspect'
        
        return 'ok'
    
    def _insert_reading(self, equipment_id: str, timestamp: str, sensor_name: str,
                       value: float, unit: str, quality_flag: str):
        """Insert sensor reading into SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO sensor_readings 
                   (equipment_id, timestamp, sensor_name, value, unit, data_quality_flag)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (equipment_id, timestamp, sensor_name, value, unit, quality_flag)
            )
            conn.commit()
            self.rows_inserted += 1
        
        except Exception as e:
            print(f"❌ Database insert error: {e}")
        
        finally:
            conn.close()
    
    def start(self):
        """Connect and start listening."""
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_forever()
    
    def print_stats(self):
        """Print statistics."""
        print(f"\n📊 Subscriber Stats:")
        print(f"  Messages received: {self.messages_received}")
        print(f"  Rows inserted: {self.rows_inserted}")
        print(f"  Errors: {self.errors}")

def main():
    """Start MQTT subscriber."""
    subscriber = MQTTSubscriber(db_path="aipms.db")
    
    try:
        print("🎧 Starting MQTT Subscriber...")
        subscriber.start()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping subscriber...")
        subscriber.print_stats()

if __name__ == "__main__":
    main()
```

---

## Phase 2A-4: Run & Verify (15 minutes)

### Step 4.1: Start All Components

```powershell
# Terminal 1: Start simulator
cd aipms-hackathon
python simulator/simulator.py

# Terminal 2: Start subscriber  
cd aipms-hackathon
python simulator/mqtt_subscriber.py

# Terminal 3: Verify in real-time
sqlite3 aipms.db "SELECT COUNT(*) as total_readings FROM sensor_readings;"
sqlite3 aipms.db "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;"
```

### Step 4.2: Verify Success Criteria

✅ **Mosquitto running:**
```powershell
docker ps | findstr aipms-mosquitto
```

✅ **Simulator publishing:**
```powershell
mosquitto_sub -h localhost -p 1883 -t "mines/equipment/+/sensors" -C 10
```

✅ **Data in database:**
```powershell
sqlite3 aipms.db "SELECT COUNT(*) FROM sensor_readings;"
sqlite3 aipms.db "SELECT DISTINCT equipment_id FROM sensor_readings;"
sqlite3 aipms.db "SELECT DISTINCT data_quality_flag FROM sensor_readings;"
```

✅ **Quality flags working:**
```powershell
sqlite3 aipms.db "SELECT * FROM sensor_readings WHERE data_quality_flag = 'suspect';"
```

---

## Phase 2A-5: Success Checkpoint

| Criterion | Expected | Verification |
|-----------|----------|---------------|
| MQTT broker running | Port 1883 listening | `netstat -ano \| findstr 1883` |
| Simulator publishing | 1 msg/sec per equipment | `mosquitto_sub` sees 3-5 msgs/sec |
| Subscriber storing | Rows increase over time | `SELECT COUNT(*)` grows |
| Data quality flagging | Some readings marked "suspect" | `WHERE data_quality_flag != 'ok'` has rows |
| 3 units active | EXC-01, DMP-03, CVR-01 | `SELECT DISTINCT equipment_id` |

---

## Rollback Procedures

**Stop everything:**
```powershell
# Stop simulator (Ctrl+C in terminal)
# Stop subscriber (Ctrl+C in terminal)

# Stop Mosquitto
docker stop aipms-mosquitto
docker rm aipms-mosquitto

# Clean database (optional)
rm aipms.db
```

**Restart cleanly:**
```powershell
# Recreate database schema
sqlite3 aipms.db < config/schema.sql

# Restart Mosquitto and simulators
```

---

## Next Steps (Phase 2B - Parallel)

While Phase 2A is running, Phase 2B (ML Data Preparation) proceeds in parallel:
- Download NASA C-MAPSS dataset
- Implement preprocessing and feature engineering
- Train anomaly detection, failure prediction, and RUL models

**Phase 2A → Phase 3:** Once both Phase 2A and 2B complete, proceed to Phase 3 (ML Models Integration).

---

## Time Budget

| Task | Planned | Actual | Status |
|------|---------|--------|--------|
| 1.1: Mosquitto config | 5 min | — | |
| 1.2: Start Mosquitto | 10 min | — | |
| 2.1: Simulator classes | 50 min | — | |
| 3.1: Subscriber class | 40 min | — | |
| 4.1-4.2: Run & verify | 15 min | — | |
| **Total** | **120 min** | — | **On Track** |

---

## Phase 2A Success = Ready for Phase 3 ✅
