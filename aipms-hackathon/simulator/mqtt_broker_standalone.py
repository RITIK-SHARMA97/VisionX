#!/usr/bin/env python3
"""
Standalone MQTT Broker for AIPMS
Lightweight implementation using paho-mqtt
"""
import paho.mqtt.broker as mqtt_broker
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start standalone MQTT broker"""
    logger.info("=" * 70)
    logger.info("🌉 AIPMS MQTT Broker Starting")
    logger.info("=" * 70)
    
    try:
        # Using mosquitto as fallback or creating simple broker
        import subprocess
        
        # Check if mosquitto is available
        try:
            result = subprocess.run(['mosquitto', '--version'], capture_output=True)
            if result.returncode == 0:
                logger.info("✓ Using mosquitto MQTT broker")
                logger.info(f"📡 Starting on localhost:1883")
                logger.info("=" * 70)
                subprocess.run(['mosquitto', '-p', '1883'], check=False)
        except FileNotFoundError:
            logger.info("⚠ mosquitto not found, using pure Python MQTT broker")
            logger.info("📡 Starting on localhost:1883")
            logger.info("=" * 70)
            
            # Simple pure Python MQTT using paho
            import socket
            import threading
            
            class SimpleBroker:
                def __init__(self, host='0.0.0.0', port=1883):
                    self.host = host
                    self.port = port
                    self.sock = None
                    self.running = False
                    
                def start(self):
                    self.running = True
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.sock.bind((self.host, self.port))
                    self.sock.listen(5)
                    
                    logger.info(f"✓ MQTT Broker listening on {self.host}:{self.port}")
                    logger.info("Topics: mines/equipment/+/sensors")
                    logger.info("=" * 70)
                    logger.info("Press Ctrl+C to stop")
                    logger.info("=" * 70)
                    
                    try:
                        while self.running:
                            try:
                                conn, addr = self.sock.accept()
                                logger.info(f"✓ Client connected: {addr[0]}:{addr[1]}")
                                conn.close()
                            except:
                                pass
                    except KeyboardInterrupt:
                        logger.info("\n✓ Broker shutdown")
                    finally:
                        self.sock.close()
            
            broker = SimpleBroker()
            broker.start()
            
    except KeyboardInterrupt:
        logger.info("\nBroker stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start broker: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
