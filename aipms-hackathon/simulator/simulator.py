"""
AIPMS Sensor Simulator
Generates realistic equipment degradation data at 1 Hz
"""
import os
import json
import time
import random
from datetime import datetime
from enum import Enum
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LifecyclePhase(str, Enum):
    """Equipment lifecycle phases"""
    HEALTHY = "healthy"
    EARLY_DEGRADATION = "early_degradation"
    ACCELERATED_DEGRADATION = "accelerated_degradation"
    IMMINENT_FAILURE = "imminent_failure"
    FAILED = "failed"

class SensorSimulator:
    """
    Simulates realistic sensor readings for equipment.
    Generates data based on lifecycle phase with appropriate degradation curves.
    """
    
    def __init__(self, equipment_id: str, equipment_type: str, mqtt_client: mqtt.Client):
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.mqtt_client = mqtt_client
        self.phase = LifecyclePhase.HEALTHY
        self.lifecycle_progress = 0.0  # 0.0 to 1.0
        
        # Sensor baselines (realistic for mining equipment)
        self.baselines = {
            'excavator': {
                'temperature': 85.0,    # °C
                'vibration': 1.5,       # mm/s RMS
                'pressure': 200.0,      # bar
                'rpm': 1500.0,          # RPM
                'fuel_consumption': 22.0  # L/hr
            },
            'dumper': {
                'temperature': 90.0,
                'vibration': 1.2,
                'pressure': 180.0,
                'rpm': 1800.0,
                'fuel_consumption': 25.0
            },
            'conveyor': {
                'temperature': 45.0,
                'vibration': 0.8,
                'pressure': 120.0,
                'rpm': 900.0,
                'fuel_consumption': 5.0
            }
        }
        
        self.current_values = self.baselines.get(equipment_type, self.baselines['dumper']).copy()
    
    def set_lifecycle_phase(self, phase: LifecyclePhase, progress: float = None):
        """Update equipment lifecycle phase"""
        self.phase = phase
        if progress is not None:
            self.lifecycle_progress = min(1.0, max(0.0, progress))
        logger.info(f"{self.equipment_id} phase: {phase.value} ({self.lifecycle_progress*100:.0f}%)")
    
    def generate_reading(self) -> dict:
        """Generate single sensor reading based on current lifecycle phase"""
        base = self.baselines.get(self.equipment_type, self.baselines['dumper'])
        
        # Apply degradation multipliers based on lifecycle phase
        if self.phase == LifecyclePhase.HEALTHY:
            temp_factor = 1.0 + random.gauss(0, 0.02)
            vib_factor = 1.0 + random.gauss(0, 0.02)
            pressure_factor = 1.0 + random.gauss(0, 0.01)
            
        elif self.phase == LifecyclePhase.EARLY_DEGRADATION:
            # Gradual increase in temperature and vibration
            progress = self.lifecycle_progress
            temp_factor = 1.0 + (0.10 * progress) + random.gauss(0, 0.02)
            vib_factor = 1.0 + (0.15 * progress) + random.gauss(0, 0.02)
            pressure_factor = 1.0 - (0.03 * progress) + random.gauss(0, 0.01)
            
        elif self.phase == LifecyclePhase.ACCELERATED_DEGRADATION:
            # Rapid increase in anomalies
            progress = self.lifecycle_progress
            temp_factor = 1.0 + (0.25 * progress) + random.gauss(0, 0.05)
            vib_factor = 1.0 + (0.40 * progress) + random.gauss(0, 0.05)
            pressure_factor = 1.0 - (0.15 * progress) + random.gauss(0, 0.03)
            
        elif self.phase == LifecyclePhase.IMMINENT_FAILURE:
            # Critical values with spikes
            temp_factor = 1.25 + random.gauss(0, 0.10)
            vib_factor = 3.0 + random.gauss(0, 0.5)
            pressure_factor = 0.6 + random.gauss(0, 0.10)
            
        else:  # FAILED
            temp_factor = 1.0
            vib_factor = 0.0
            pressure_factor = 0.0
        
        # Update current values
        self.current_values['temperature'] = max(40, min(150, base['temperature'] * temp_factor))
        self.current_values['vibration'] = max(0, base['vibration'] * vib_factor)
        self.current_values['pressure'] = max(0, base['pressure'] * pressure_factor)
        self.current_values['rpm'] = base['rpm'] * (0.95 + random.gauss(0, 0.05))
        self.current_values['fuel_consumption'] = base['fuel_consumption'] * (1.0 + random.gauss(0, 0.1))
        
        return {
            'equipment_id': self.equipment_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'temperature': round(self.current_values['temperature'], 1),
            'vibration': round(self.current_values['vibration'], 2),
            'pressure': round(self.current_values['pressure'], 1),
            'rpm': round(self.current_values['rpm'], 0),
            'fuel_consumption': round(self.current_values['fuel_consumption'], 1)
        }
    
    def publish(self, reading: dict):
        """Publish reading to MQTT"""
        topic = f"mines/equipment/{self.equipment_id}/sensors"
        payload = json.dumps(reading)
        self.mqtt_client.publish(topic, payload, qos=1)
        logger.debug(f"Published {self.equipment_id}: {reading}")


def connect_mqtt() -> mqtt.Client:
    """Connect to MQTT broker"""
    client = mqtt.Client()
    broker = os.getenv('MQTT_HOST', 'localhost')
    port = int(os.getenv('MQTT_PORT', 1883))
    
    try:
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        logger.info(f"Connected to MQTT broker at {broker}:{port}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")
        raise


if __name__ == "__main__":
    # Initialize MQTT
    mqtt_client = connect_mqtt()
    time.sleep(2)  # Wait for connection
    
    # Create simulators for 3 equipment units
    simulators = [
        SensorSimulator("EXC-01", "excavator", mqtt_client),
        SensorSimulator("DMP-03", "dumper", mqtt_client),
        SensorSimulator("CVR-01", "conveyor", mqtt_client)
    ]
    
    # Set initial lifecycle phases for demo
    simulators[0].set_lifecycle_phase(LifecyclePhase.ACCELERATED_DEGRADATION, 0.90)
    simulators[1].set_lifecycle_phase(LifecyclePhase.EARLY_DEGRADATION, 0.70)
    simulators[2].set_lifecycle_phase(LifecyclePhase.HEALTHY, 0.30)
    
    hz = int(os.getenv('SIMULATOR_HZ', 1))
    interval = 1.0 / hz
    
    logger.info(f"Starting sensor simulator at {hz} Hz")
    
    try:
        while True:
            for simulator in simulators:
                reading = simulator.generate_reading()
                simulator.publish(reading)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Simulator stopped")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
