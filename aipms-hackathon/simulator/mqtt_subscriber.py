"""
MQTT Subscriber for AIPMS
Subscribes to equipment sensor topics and writes readings to SQLite database
"""
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.orm import Base, Equipment, SensorReading
import threading
import os

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./aipms.db')


class MQTTSubscriber:
    """Subscribes to MQTT topics and persists sensor readings to database"""
    
    def __init__(self, broker_host='localhost', broker_port=1883, db_url=DATABASE_URL):
        """
        Initialize MQTT subscriber
        
        Args:
            broker_host: MQTT broker hostname (default: localhost)
            broker_port: MQTT broker port (default: 1883)
            db_url: SQLAlchemy database URL
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.db_url = db_url
        
        # Set up database
        self.engine = create_engine(db_url, connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # MQTT client (paho-mqtt 1.6.x compatible)
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Stats
        self.messages_received = 0
        self.messages_persisted = 0
        self.messages_failed = 0
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Called when MQTT client connects to broker"""
        if rc == 0:
            logger.info(f"MQTT connected to {self.broker_host}:{self.broker_port}")
            # Subscribe to all equipment sensor topics
            client.subscribe("mines/equipment/+/sensors")
            logger.info("Subscribed to mines/equipment/+/sensors")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Called when MQTT client disconnects"""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection with code {rc}")
        else:
            logger.info("MQTT disconnected (graceful)")
    
    def on_message(self, client, userdata, msg):
        """
        Called when MQTT message is received
        Expects payload: {"equipment_id": "EXC-01", "timestamp": "2025-04-18T12:34:56", 
                          "sensor_name": "temperature", "value": 75.5, "unit": "°C"}
        """
        self.messages_received += 1
        
        try:
            # Parse payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            equipment_id = payload.get('equipment_id')
            timestamp_str = payload.get('timestamp')
            sensor_name = payload.get('sensor_name')
            value = payload.get('value')
            unit = payload.get('unit', '')
            
            # Validate required fields
            if not all([equipment_id, timestamp_str, sensor_name, value is not None]):
                logger.warning(f"Invalid payload (missing fields): {payload}")
                self.messages_failed += 1
                return
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.utcnow()
            
            # Get or create equipment in database
            session = self.SessionLocal()
            try:
                equipment = session.query(Equipment).filter_by(id=equipment_id).first()
                if not equipment:
                    # Extract type from equipment_id pattern (EXC-01 -> excavator)
                    type_map = {'EXC': 'excavator', 'DMP': 'dumper', 'CVR': 'conveyor', 'DRL': 'drill'}
                    eq_type = type_map.get(equipment_id[:3], 'unknown')
                    equipment = Equipment(
                        id=equipment_id,
                        name=f"{eq_type.capitalize()} {equipment_id}",
                        type=eq_type,
                        location="Mine Site",
                        status="normal"
                    )
                    session.add(equipment)
                    session.commit()
                    logger.info(f"Created new equipment: {equipment_id}")
                
                # Create sensor reading record
                reading = SensorReading(
                    equipment_id=equipment_id,
                    timestamp=timestamp,
                    sensor_name=sensor_name,
                    value=value,
                    unit=unit,
                    data_quality_flag='ok'
                )
                session.add(reading)
                session.commit()
                
                self.messages_persisted += 1
                
                if self.messages_persisted % 100 == 0:
                    logger.info(f"Persisted {self.messages_persisted} readings | "
                               f"Received {self.messages_received} | "
                               f"Failed {self.messages_failed}")
                
            except Exception as e:
                logger.error(f"Database error: {e}")
                self.messages_failed += 1
                session.rollback()
            finally:
                session.close()
        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON payload: {msg.payload}")
            self.messages_failed += 1
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.messages_failed += 1
    
    def start(self):
        """Start MQTT subscriber (blocking)"""
        self.running = True
        logger.info(f"Starting MQTT subscriber on {self.broker_host}:{self.broker_port}")
        
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_forever()
        except Exception as e:
            logger.error(f"Failed to start subscriber: {e}")
            self.running = False
    
    def start_async(self):
        """Start MQTT subscriber in background thread (non-blocking)"""
        self.running = True
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        logger.info(f"MQTT subscriber started in background thread")
        return thread
    
    def stop(self):
        """Stop MQTT subscriber"""
        self.running = False
        self.client.disconnect()
        logger.info(f"MQTT subscriber stopped. "
                   f"Stats: {self.messages_persisted} persisted, "
                   f"{self.messages_failed} failed out of "
                   f"{self.messages_received} received")


def main():
    """Run MQTT subscriber"""
    subscriber = MQTTSubscriber()
    
    logger.info("=" * 70)
    logger.info("AIPMS MQTT Subscriber - Phase 2A")
    logger.info("=" * 70)
    logger.info(f"Broker: {subscriber.broker_host}:{subscriber.broker_port}")
    logger.info(f"Database: {subscriber.db_url}")
    logger.info("Topics: mines/equipment/+/sensors")
    logger.info("=" * 70)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70)
    
    try:
        subscriber.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        subscriber.stop()


if __name__ == "__main__":
    main()
