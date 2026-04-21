"""MQTT sensor simulator for AIPMS - publishes realistic sensor streams."""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime
import logging
import config_constants as cfg
from typing import Optional
from .equipment_profiles import EquipmentProfile

logging.basicConfig(level=cfg.LOG_LEVEL, format=cfg.LOG_FORMAT)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """Publishes sensor readings from an equipment unit to MQTT broker."""
    
    def __init__(self, equipment_id: str, lifecycle_stage: str, 
                 broker_host: Optional[str] = None, broker_port: Optional[int] = None) -> None:
        """
        Initialize sensor simulator.
        
        Args:
            equipment_id: Equipment identifier (e.g., 'EXC-01')
            lifecycle_stage: Equipment degradation stage
            broker_host: MQTT broker hostname (default from config)
            broker_port: MQTT broker port (default from config)
        """
        self.equipment_id = equipment_id
        self.lifecycle_stage = lifecycle_stage
        self.profile = EquipmentProfile(equipment_id, lifecycle_stage)
        self.client = mqtt.Client(client_id=f"sim-{equipment_id}")
        self.broker_host = broker_host or cfg.MQTT_BROKER_HOST
        self.broker_port = broker_port or cfg.MQTT_BROKER_PORT
        self.running: bool = False
        self.published_count: int = 0
        
        # Set MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc) -> None:
        """MQTT connection callback."""
        if rc == 0:
            logger.info(f"[{self.equipment_id}] Connected to MQTT broker ({self.broker_host}:{self.broker_port})")
            self.running = True
        else:
            logger.error(f"[{self.equipment_id}] MQTT connection failed with code {rc}")
            self.running = False
    
    def on_disconnect(self, client, userdata, rc) -> None:
        """MQTT disconnection callback."""
        if rc != 0:
            logger.warning(f"[{self.equipment_id}] Unexpected disconnection: {rc}")
        self.running = False
    
    def on_publish(self, client, userdata, mid) -> None:
        """MQTT publish callback."""
        # Called after message is published
        logger.debug(f"[{self.equipment_id}] Message {mid} published")
    
    def start(self) -> None:
        """Connect to MQTT broker and start background thread."""
        try:
            logger.debug(f"[{self.equipment_id}] Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, cfg.MQTT_BROKER_TIMEOUT)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"[{self.equipment_id}] Failed to connect: {e}")
    
    def publish_loop(self, hz: float = 1.0) -> None:
        """
        Publish sensor readings at specified frequency.
        
        Args:
            hz: Publishing frequency in Hz (default: 1 message per second)
        """
        interval = 1.0 / hz
        
        logger.info(f"[{self.equipment_id}] Publishing at {hz} Hz (interval: {interval:.2f}s)")
        
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
                        self.client.publish(topic, json.dumps(payload), qos=cfg.MQTT_PUBLISH_QOS)
                        self.published_count += 1
                        logger.debug(f"[{self.equipment_id}] Published {reading.sensor_name}")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"[{self.equipment_id}] Publish error: {e}")
    
    def stop(self) -> None:
        """Gracefully shutdown simulator."""
        logger.info(f"[{self.equipment_id}] Stopping simulator... (published {self.published_count} messages)")
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()


def main() -> None:
    """Run AIPMS sensor simulators for multiple equipment units."""
    
    logger.info("=" * 70)
    logger.info("AIPMS Sensor Simulator - Phase 2A")
    logger.info("=" * 70)
    
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
    logger.info("Starting simulators...")
    
    for config in equipment_config:
        eq_id = config['id']
        stage = config['stage']
        desc = config['description']
        
        logger.info(f"  {eq_id:10} | {stage:25} | {desc}")
        
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
    logger.info("=" * 70)
    logger.info("All simulators started successfully!")
    logger.info("")
    logger.info("Publishing configuration:")
    logger.info(f"  • MQTT Broker: {cfg.MQTT_BROKER_HOST}:{cfg.MQTT_BROKER_PORT}")
    logger.info(f"  • Publishing Frequency: 1 Hz (1 message/second per equipment)")
    logger.info(f"  • Topic Pattern: mines/equipment/{{equipment_id}}/sensors")
    logger.info(f"  • QoS: {cfg.MQTT_PUBLISH_QOS}")
    logger.info("")
    logger.info("To verify in another terminal:")
    logger.info(f"  mosquitto_sub -h {cfg.MQTT_BROKER_HOST} -p {cfg.MQTT_BROKER_PORT} -t 'mines/equipment/+/sensors' -v")
    logger.info("")
    logger.info("Press Ctrl+C to stop all simulators")
    logger.info("=" * 70)
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("")
        logger.info("=" * 70)
        logger.info("Shutting down simulators...")
        logger.info("=" * 70)
        
        # Stop all simulators
        for sim in simulators:
            sim.stop()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=2)
        
        logger.info("All simulators stopped")
        logger.info("")


# Export alias for backward compatibility
SimulatorEngine = SensorSimulator


if __name__ == "__main__":
    main()
