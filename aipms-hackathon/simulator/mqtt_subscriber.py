"""
AIPMS MQTT Subscriber
Consumes sensor data from MQTT and writes to SQLite
"""
import os
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./aipms.db')

class MQTTSubscriber:
    """MQTT subscriber for sensor data ingestion"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.client = mqtt.Client()
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup MQTT callbacks"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            client.subscribe("mines/equipment/+/sensors")
        else:
            logger.error(f"Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """MQTT message callback - process incoming sensor data"""
        try:
            payload = json.loads(msg.payload.decode())
            self.process_sensor_reading(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection: {rc}")
    
    def process_sensor_reading(self, data: dict):
        """Process and store sensor reading"""
        try:
            # Data quality checks
            equipment_id = data.get('equipment_id')
            if not equipment_id:
                logger.warning("Missing equipment_id in sensor reading")
                return
            
            # Extract sensor fields
            sensors = {
                'temperature': data.get('temperature'),
                'vibration': data.get('vibration'),
                'pressure': data.get('pressure'),
                'rpm': data.get('rpm'),
                'fuel_consumption': data.get('fuel_consumption')
            }
            
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            
            # Store readings (simplified - full ORM integration in Phase 3)
            logger.info(f"{equipment_id}: temp={sensors['temperature']}°C, "
                       f"vib={sensors['vibration']}mm/s, "
                       f"pressure={sensors['pressure']}bar")
            
        except Exception as e:
            logger.error(f"Error processing reading: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        broker = os.getenv('MQTT_HOST', 'localhost')
        port = int(os.getenv('MQTT_PORT', 1883))
        
        try:
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT subscriber connected to {broker}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT subscriber disconnected")


if __name__ == "__main__":
    subscriber = MQTTSubscriber()
    
    try:
        subscriber.connect()
        logger.info("MQTT subscriber running (Press Ctrl+C to stop)")
        subscriber.client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Subscriber stopped")
        subscriber.disconnect()
