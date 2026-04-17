"""MQTT sensor simulator for AIPMS - publishes realistic sensor streams."""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime
from equipment_profiles import EquipmentProfile


class SensorSimulator:
    """Publishes sensor readings from an equipment unit to MQTT broker."""
    
    def __init__(self, equipment_id: str, lifecycle_stage: str, 
                 broker_host: str = "localhost", broker_port: int = 1883):
        """
        Initialize sensor simulator.
        
        Args:
            equipment_id: Equipment identifier (e.g., 'EXC-01')
            lifecycle_stage: Equipment degradation stage
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port (default: 1883)
        """
        self.equipment_id = equipment_id
        self.lifecycle_stage = lifecycle_stage
        self.profile = EquipmentProfile(equipment_id, lifecycle_stage)
        self.client = mqtt.Client(client_id=f"sim-{equipment_id}")
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.running = False
        self.published_count = 0
        
        # Set MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback."""
        if rc == 0:
            print(f"✅ [{self.equipment_id}] Connected to MQTT broker ({self.broker_host}:{self.broker_port})")
            self.running = True
        else:
            print(f"❌ [{self.equipment_id}] MQTT connection failed with code {rc}")
            self.running = False
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback."""
        if rc != 0:
            print(f"⚠️  [{self.equipment_id}] Unexpected disconnection: {rc}")
        self.running = False
    
    def on_publish(self, client, userdata, mid):
        """MQTT publish callback."""
        # Called after message is published
        pass
    
    def start(self):
        """Connect to MQTT broker and start background thread."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ [{self.equipment_id}] Failed to connect: {e}")
    
    def publish_loop(self, hz: float = 1.0):
        """
        Publish sensor readings at specified frequency.
        
        Args:
            hz: Publishing frequency in Hz (default: 1 message per second)
        """
        interval = 1.0 / hz
        
        print(f"📡 [{self.equipment_id}] Publishing at {hz} Hz (interval: {interval:.2f}s)")
        
        while True:
            try:
                if self.running:
                    # Generate readings for all sensors
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
                        self.published_count += 1
                
                time.sleep(interval)
            
            except Exception as e:
                print(f"❌ [{self.equipment_id}] Publish error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Gracefully shutdown simulator."""
        print(f"⏹️  [{self.equipment_id}] Stopping simulator... (published {self.published_count} messages)")
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()


def main():
    """Run AIPMS sensor simulators for multiple equipment units."""
    
    print("=" * 70)
    print("🚀 AIPMS Sensor Simulator - Phase 2A")
    print("=" * 70)
    print()
    
    # Define equipment units with different degradation stages
    equipment_config = [
        {
            'id': 'EXC-01',
            'stage': 'accelerated_degradation',
            'description': 'Rope Shovel - Will trigger alerts in ~3 minutes'
        },
        {
            'id': 'DMP-03',
            'stage': 'early_degradation',
            'description': 'Dump Truck - Early warning stage'
        },
        {
            'id': 'CVR-01',
            'stage': 'healthy',
            'description': 'Conveyor Belt - Normal operation'
        },
    ]
    
    simulators = []
    threads = []
    
    # Start all simulators
    print("Starting simulators...")
    print()
    
    for config in equipment_config:
        eq_id = config['id']
        stage = config['stage']
        desc = config['description']
        
        print(f"  {eq_id:10} | {stage:25} | {desc}")
        
        # Create simulator
        sim = SensorSimulator(eq_id, stage)
        sim.start()
        
        # Start publish loop in background thread
        t = threading.Thread(
            target=sim.publish_loop,
            args=(1.0,),  # 1 Hz = 1 message per second
            daemon=True,
            name=f"sim-{eq_id}"
        )
        t.start()
        
        simulators.append(sim)
        threads.append(t)
        
        time.sleep(0.5)  # Stagger starts slightly
    
    print()
    print("=" * 70)
    print("✅ All simulators started successfully!")
    print()
    print("📊 Publishing configuration:")
    print(f"  • MQTT Broker: localhost:1883")
    print(f"  • Publishing Frequency: 1 Hz (1 message/second per equipment)")
    print(f"  • Topic Pattern: mines/equipment/{{equipment_id}}/sensors")
    print(f"  • Total Messages/Second: 5 (5 sensors × 3 equipment × 1 Hz)")
    print()
    print("🎧 To verify in another terminal:")
    print("  mosquitto_sub -h localhost -p 1883 -t 'mines/equipment/+/sensors' -v")
    print()
    print("⏹️  Press Ctrl+C to stop all simulators")
    print("=" * 70)
    print()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 70)
        print("⏹️  Shutting down simulators...")
        print("=" * 70)
        
        # Stop all simulators
        for sim in simulators:
            sim.stop()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=2)
        
        print("✅ All simulators stopped")
        print()


if __name__ == "__main__":
    main()
