#!/usr/bin/env python3
"""
IoT Sensor Simulator for AIPMS
Publishes realistic sensor data to MQTT broker at 1 Hz
"""
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
from datetime import datetime
import random
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'mines/equipment/{}/sensors'
PUBLISH_FREQUENCY = 1  # Hz


class EquipmentSimulator:
    """Simulates sensor readings for mining equipment"""
    
    def __init__(self, equipment_id, equipment_type='excavator'):
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.client = mqtt.Client(client_id=f"sim-{equipment_id}")
        self.running = False
        self.message_count = 0
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Sensor ranges for different equipment types
        self.sensor_ranges = self._get_sensor_ranges()
    
    def _get_sensor_ranges(self):
        """Get typical sensor ranges for equipment type"""
        ranges = {
            'excavator': {
                'temperature': (60, 90),    # °C
                'vibration': (0.5, 3.5),   # mm/s
                'pressure': (150, 350),    # bar
                'rpm': (200, 500)          # rpm
            },
            'dumper': {
                'temperature': (50, 100),
                'vibration': (0.3, 2.5),
                'pressure': (200, 400),
                'rpm': (300, 1200)
            },
            'conveyor': {
                'temperature': (40, 80),
                'vibration': (0.1, 1.5),
                'pressure': (100, 250),
                'rpm': (100, 300)
            }
        }
        return ranges.get(self.equipment_type, ranges['excavator'])
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.running = True
            logger.info(f"✓ [{self.equipment_id}] Connected to MQTT broker")
        else:
            logger.error(f"✗ [{self.equipment_id}] Connection failed with code {rc}")
            self.running = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        if rc != 0:
            logger.warning(f"⚠ [{self.equipment_id}] Unexpected disconnection")
        self.running = False
    
    def on_publish(self, client, userdata, mid):
        """Callback after message is published"""
        self.message_count += 1
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"[{self.equipment_id}] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
        except Exception as e:
            logger.error(f"✗ [{self.equipment_id}] Connection failed: {e}")
            return False
        return True
    
    def generate_readings(self):
        """Generate realistic sensor readings"""
        readings = []
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        for sensor_name, (min_val, max_val) in self.sensor_ranges.items():
            # Add some noise to readings
            value = random.uniform(min_val, max_val)
            
            # Get appropriate unit
            units = {
                'temperature': '°C',
                'vibration': 'mm/s',
                'pressure': 'bar',
                'rpm': 'rpm'
            }
            unit = units.get(sensor_name, '')
            
            readings.append({
                'equipment_id': self.equipment_id,
                'timestamp': timestamp,
                'sensor_name': sensor_name,
                'value': round(value, 2),
                'unit': unit
            })
        
        return readings
    
    def publish_readings(self, hz=1.0):
        """Publish sensor readings at specified frequency"""
        interval = 1.0 / hz
        logger.info(f"[{self.equipment_id}] Publishing at {hz} Hz (every {interval:.2f}s)")
        
        while self.running:
            try:
                readings = self.generate_readings()
                
                for reading in readings:
                    topic = MQTT_TOPIC.format(self.equipment_id)
                    payload = json.dumps(reading)
                    self.client.publish(topic, payload, qos=1)
                
                if self.message_count % 10 == 0:
                    logger.info(f"[{self.equipment_id}] Published {self.message_count} messages")
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"✗ [{self.equipment_id}] Publish error: {e}")
                break
    
    def stop(self):
        """Stop simulator"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info(f"[{self.equipment_id}] Stopped (published {self.message_count} messages)")


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🔧 AIPMS Sensor Simulator - IoT Data Generator")
    logger.info("=" * 70)
    
    # Equipment to simulate
    equipment = [
        {'id': 'EXC-01', 'type': 'excavator', 'desc': 'Rope Shovel Excavator'},
        {'id': 'DMP-03', 'type': 'dumper', 'desc': 'Dump Truck'},
        {'id': 'CVR-01', 'type': 'conveyor', 'desc': 'Conveyor Belt'},
    ]
    
    simulators = []
    threads = []
    
    # Start all simulators
    logger.info(f"\nStarting {len(equipment)} equipment simulators...\n")
    
    for eq in equipment:
        sim = EquipmentSimulator(eq['id'], eq['type'])
        
        if not sim.connect():
            logger.error(f"Skipping {eq['id']}")
            continue
        
        # Start publishing in background thread
        thread = threading.Thread(
            target=sim.publish_readings,
            args=(PUBLISH_FREQUENCY,),
            daemon=True,
            name=f"sim-{eq['id']}"
        )
        thread.start()
        
        simulators.append(sim)
        threads.append(thread)
        logger.info(f"✓ {eq['id']:10} | {eq['desc']}")
        time.sleep(0.5)
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ All simulators started successfully!")
    logger.info("=" * 70)
    logger.info(f"📊 Publishing to: mines/equipment/{{equipment_id}}/sensors")
    logger.info(f"📈 Frequency: {PUBLISH_FREQUENCY} Hz")
    logger.info(f"📍 Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info("=" * 70)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\nShutting down simulators...")
        for sim in simulators:
            sim.stop()
        logger.info("✓ All simulators stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
