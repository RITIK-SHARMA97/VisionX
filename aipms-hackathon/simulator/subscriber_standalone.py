#!/usr/bin/env python3
"""
MQTT Subscriber for AIPMS
Listens for sensor data and writes to SQLite database
"""
import paho.mqtt.client as mqtt
import json
import logging
import sys
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'mines/equipment/+/sensors'

# Database
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api.orm import Base, Equipment, SensorReading
    DB_AVAILABLE = True
except ImportError:
    logger.warning("⚠ SQLAlchemy not available - will log to console only")
    DB_AVAILABLE = False

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./aipms.db')


class MQTTSubscriber:
    """Subscribes to MQTT sensor data and persists to database"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="subscriber-aipms")
        self.running = False
        self.messages_received = 0
        self.messages_persisted = 0
        self.messages_failed = 0
        
        # Database setup
        if DB_AVAILABLE:
            self.engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected"""
        if rc == 0:
            self.running = True
            logger.info(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC, qos=1)
            logger.info(f"✓ Subscribed to: {MQTT_TOPIC}")
        else:
            logger.error(f"✗ Connection failed with code {rc}")
            self.running = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        if rc != 0:
            logger.warning(f"⚠ Unexpected disconnection (code {rc})")
        else:
            logger.info("✓ Graceful disconnect")
        self.running = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        self.messages_received += 1
        
        try:
            # Parse MQTT message
            payload = json.loads(msg.payload.decode('utf-8'))
            
            equipment_id = payload.get('equipment_id')
            timestamp_str = payload.get('timestamp')
            sensor_name = payload.get('sensor_name')
            value = payload.get('value')
            unit = payload.get('unit', '')
            
            # Validate
            if not all([equipment_id, timestamp_str, sensor_name, value is not None]):
                logger.warning(f"⚠ Invalid message (missing fields)")
                self.messages_failed += 1
                return
            
            # Log to console
            logger.info(f"📊 {equipment_id} | {sensor_name}: {value} {unit}")
            
            # Persist to database if available
            if DB_AVAILABLE:
                try:
                    session = self.SessionLocal()
                    
                    # Ensure equipment exists
                    equipment = session.query(Equipment).filter_by(id=equipment_id).first()
                    if not equipment:
                        type_map = {'EXC': 'excavator', 'DMP': 'dumper', 'CVR': 'conveyor', 'DRL': 'drill'}
                        eq_type = type_map.get(equipment_id[:3], 'unknown')
                        equipment = Equipment(
                            id=equipment_id,
                            name=f"{eq_type.title()} {equipment_id}",
                            type=eq_type,
                            location="Mine Site",
                            status="normal"
                        )
                        session.add(equipment)
                        session.commit()
                        logger.info(f"✓ Created equipment: {equipment_id}")
                    
                    # Create reading record
                    reading = SensorReading(
                        equipment_id=equipment_id,
                        timestamp=datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')),
                        sensor_name=sensor_name,
                        value=value,
                        unit=unit,
                        data_quality_flag='ok'
                    )
                    session.add(reading)
                    session.commit()
                    
                    self.messages_persisted += 1
                    
                    # Show progress
                    if self.messages_persisted % 50 == 0:
                        logger.info(f"\n📈 Database Stats:")
                        logger.info(f"   ✓ Persisted: {self.messages_persisted}")
                        logger.info(f"   ⚠ Failed: {self.messages_failed}")
                        logger.info(f"   📥 Received: {self.messages_received}\n")
                    
                    session.close()
                
                except Exception as e:
                    logger.error(f"✗ Database error: {e}")
                    self.messages_failed += 1
            
        except json.JSONDecodeError:
            logger.warning(f"⚠ Invalid JSON payload")
            self.messages_failed += 1
        except Exception as e:
            logger.error(f"✗ Error processing message: {e}")
            self.messages_failed += 1
    
    def start(self):
        """Start subscriber (blocking)"""
        try:
            logger.info("=" * 70)
            logger.info("🔌 AIPMS MQTT Subscriber - IoT Data Persister")
            logger.info("=" * 70)
            logger.info(f"📍 Broker: {MQTT_BROKER}:{MQTT_PORT}")
            logger.info(f"📥 Topic: {MQTT_TOPIC}")
            
            if DB_AVAILABLE:
                logger.info(f"💾 Database: {DATABASE_URL}")
            else:
                logger.info("💾 Database: Disabled (console logging only)")
            
            logger.info("=" * 70)
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 70 + "\n")
            
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_forever()
        
        except Exception as e:
            logger.error(f"✗ Subscriber error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n\nShutting down subscriber...")
            self.stop()
    
    def stop(self):
        """Stop subscriber"""
        self.running = False
        self.client.disconnect()
        
        logger.info("=" * 70)
        logger.info("✓ Subscriber stopped")
        logger.info("=" * 70)
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   ✓ Persisted: {self.messages_persisted}")
        logger.info(f"   ⚠ Failed: {self.messages_failed}")
        logger.info(f"   📥 Received: {self.messages_received}")
        logger.info("=" * 70)


def main():
    """Main entry point"""
    subscriber = MQTTSubscriber()
    
    try:
        subscriber.start()
    except KeyboardInterrupt:
        subscriber.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
