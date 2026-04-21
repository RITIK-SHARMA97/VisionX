"""AIPMS Simulator Package - IoT sensor simulation & MQTT publishing."""

# Export core simulator classes
from .simulator import SensorSimulator
from .mqtt_subscriber import MQTTSubscriber
from .equipment_profiles import EquipmentProfile

# Alias for backward compatibility with test imports
SimulatorEngine = SensorSimulator

__all__ = [
    'SensorSimulator',
    'SimulatorEngine',
    'MQTTSubscriber', 
    'EquipmentProfile'
]