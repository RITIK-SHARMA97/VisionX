"""
Lightweight MQTT broker for local development/testing
Uses paho-mqtt to provide basic pub/sub functionality
"""

import socket
import threading
import logging
import json
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleMQTTBroker:
    """
    Minimal MQTT broker implementation using raw sockets
    Handles basic CONNECT, SUBSCRIBE, PUBLISH, and DISCONNECT packets
    Sufficient for local testing of AIPMS IoT pipeline
    """
    
    def __init__(self, host='localhost', port=1883):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # {client_socket: {"id": client_id, "subscriptions": [topics]}}
        self.subscriptions = defaultdict(list)  # {topic: [client_sockets]}
        self.lock = threading.Lock()
    
    def start(self):
        """Start the MQTT broker"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        logger.info("=" * 70)
        logger.info("🌉 AIPMS MQTT Broker - Lightweight Python Implementation")
        logger.info("=" * 70)
        logger.info(f"📡 Listening on {self.host}:{self.port}")
        logger.info("Topics: mines/equipment/+/sensors")
        logger.info("=" * 70)
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    logger.info(f"✓ Client connected: {address[0]}:{address[1]}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    if self.running:
                        logger.error(f"Accept error: {e}")
        except KeyboardInterrupt:
            logger.info("\nShutdown requested")
        finally:
            self.stop()
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection"""
        client_id = f"client_{address[0]}_{address[1]}"
        
        with self.lock:
            self.clients[client_socket] = {"id": client_id, "subscriptions": []}
        
        try:
            # Simple read-write loop
            buffer = b''
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    
                    if not data:
                        break
                    
                    buffer += data
                    
                    # Basic packet parsing (simplified MQTT)
                    # This is a demo - real MQTT protocol is more complex
                    try:
                        # Try to parse as JSON payload (our sensor format)
                        messages = buffer.split(b'\n')
                        buffer = b''
                        
                        for msg in messages:
                            if msg:
                                try:
                                    payload = json.loads(msg.decode('utf-8'))
                                    self._on_publish(payload, client_socket)
                                except json.JSONDecodeError:
                                    # Not JSON - might be topic subscription
                                    topic_str = msg.decode('utf-8', errors='ignore').strip()
                                    if topic_str.startswith('SUB:'):
                                        topic = topic_str.replace('SUB:', '')
                                        self._on_subscribe(client_socket, topic)
                                    elif topic_str == 'PING':
                                        client_socket.send(b'PONG\n')
                    except Exception as e:
                        logger.debug(f"Parse error: {e}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Read error from {client_id}: {e}")
                    break
        finally:
            self._disconnect_client(client_socket, client_id)
    
    def _on_subscribe(self, client_socket, topic):
        """Handle subscription request"""
        with self.lock:
            if client_socket in self.clients:
                self.clients[client_socket]['subscriptions'].append(topic)
                self.subscriptions[topic].append(client_socket)
        
        logger.info(f"✓ Client subscribed to: {topic}")
    
    def _on_publish(self, payload, publisher_socket):
        """Handle publish request - distribute to subscribers"""
        topic = payload.get('topic', 'mines/equipment/unknown/sensors')
        equipment_id = payload.get('equipment_id', 'UNKNOWN')
        sensor_name = payload.get('sensor_name', 'unknown')
        value = payload.get('value', 0)
        
        # Log the message
        logger.info(f"📨 [{equipment_id}/{sensor_name}] {value}")
        
        # Broadcast to matching subscribers (simplified - doesn't handle wildcards properly)
        message = json.dumps(payload).encode('utf-8') + b'\n'
        
        with self.lock:
            # Send to clients subscribed to this topic
            topic_pattern = 'mines/equipment/+/sensors'
            if topic_pattern in self.subscriptions:
                for client_socket in self.subscriptions[topic_pattern]:
                    if client_socket != publisher_socket and client_socket in self.clients:
                        try:
                            client_socket.send(message)
                        except Exception as e:
                            logger.debug(f"Send error: {e}")
    
    def _disconnect_client(self, client_socket, client_id):
        """Handle client disconnection"""
        logger.info(f"✗ Client disconnected: {client_id}")
        
        with self.lock:
            if client_socket in self.clients:
                subs = self.clients[client_socket].get('subscriptions', [])
                del self.clients[client_socket]
                
                # Remove from subscriptions
                for topic in subs:
                    if client_socket in self.subscriptions[topic]:
                        self.subscriptions[topic].remove(client_socket)
        
        try:
            client_socket.close()
        except:
            pass
    
    def stop(self):
        """Stop the broker"""
        self.running = False
        
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("🛑 Broker stopped")


def main():
    """Run the MQTT broker"""
    broker = SimpleMQTTBroker(host='localhost', port=1883)
    
    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Stopping broker...")
        broker.stop()


if __name__ == "__main__":
    main()
