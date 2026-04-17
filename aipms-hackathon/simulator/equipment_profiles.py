"""Equipment degradation profiles for AIPMS simulator."""

import math
import random
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SensorReading:
    """Single sensor reading with metadata."""
    equipment_id: str
    timestamp: str  # ISO-8601
    sensor_name: str
    value: float
    unit: str


class EquipmentProfile:
    """Simulates equipment with lifecycle-based degradation curves."""
    
    def __init__(self, equipment_id: str, lifecycle_stage: str):
        """
        Initialize equipment profile.
        
        Args:
            equipment_id: Equipment identifier (e.g., 'EXC-01')
            lifecycle_stage: One of: healthy, early_degradation, accelerated_degradation, imminent_failure
        """
        self.equipment_id = equipment_id
        self.lifecycle_stage = lifecycle_stage
        
        # Lifecycle progress (0.0 to 1.0) - determines severity of degradation
        self.progress = {
            'healthy': 0.3,
            'early_degradation': 0.7,
            'accelerated_degradation': 0.90,
            'imminent_failure': 0.99
        }.get(lifecycle_stage, 0.3)
        
        # Sensor baseline values (mining equipment specs from Agents.md Section 11.4)
        self.baselines = {
            'temperature_C': 75.0,          # Engine block baseline
            'vibration_mm_s': 1.2,          # Normal vibration RMS
            'hydraulic_pressure_bar': 200.0,  # System nominal pressure
            'rpm': 1400.0,                  # Rated speed
            'fuel_consumption_L_hr': 20.0,  # Baseline consumption
        }
        
        # Sensor thresholds for validation (warning/critical)
        self.thresholds = {
            'temperature_C': {'warning': 105, 'critical': 115},
            'vibration_mm_s': {'warning': 3.5, 'critical': 6.0},
            'hydraulic_pressure_bar': {'warning': 160, 'critical': 140},
            'rpm': {'warning': (900, 2100), 'critical': (700, 2400)},
            'fuel_consumption_L_hr': {'warning': 30, 'critical': 38},
        }
        
        self.cycle_count = 0
    
    def get_sensor_value(self, sensor_name: str) -> float:
        """
        Generate degradation-aware sensor value based on lifecycle stage.
        
        Args:
            sensor_name: Name of the sensor
            
        Returns:
            Realistic sensor value with degradation and noise
        """
        if sensor_name not in self.baselines:
            return 0.0
        
        base = self.baselines[sensor_name]
        noise = random.gauss(0, base * 0.02)  # 2% Gaussian noise
        
        # Apply lifecycle-based degradation multiplier
        multiplier = self._get_lifecycle_multiplier(sensor_name)
        
        value = base * multiplier + noise
        return max(0.0, value)
    
    def _get_lifecycle_multiplier(self, sensor_name: str) -> float:
        """
        Calculate degradation multiplier based on equipment lifecycle stage.
        
        Stages:
        - healthy (0.3): Baseline ± 1% noise
        - early_degradation (0.7): Linear +5% drift
        - accelerated_degradation (0.90): Exponential rise + spike events
        - imminent_failure (0.99): Extreme values + frequent anomalies
        
        Args:
            sensor_name: Sensor identifier
            
        Returns:
            Multiplier to apply to baseline value
        """
        progress = self.progress
        
        if self.lifecycle_stage == 'healthy':
            # Normal operation - minimal drift
            return 1.0 + random.gauss(0, 0.01)
        
        elif self.lifecycle_stage == 'early_degradation':
            # Slow linear drift over lifecycle
            drift = progress * 0.05  # +5% over full lifecycle
            return 1.0 + drift + random.gauss(0, 0.02)
        
        elif self.lifecycle_stage == 'accelerated_degradation':
            # Exponential rise + intermittent spike events (15% probability)
            drift = math.exp((progress - 0.7) * 5) * 0.20  # Exponential rise
            spike = 0.1 if random.random() < 0.15 else 0  # 15% spike events
            return 1.0 + drift + spike + random.gauss(0, 0.03)
        
        elif self.lifecycle_stage == 'imminent_failure':
            # Extreme behavior - severe anomalies (30% probability)
            if random.random() < 0.3:
                return random.uniform(0.0, 0.3)  # Near-zero (failure imminent)
            return 2.0 + random.gauss(0, 0.5)  # Wild swings
        
        return 1.0
    
    def generate_readings(self) -> List[SensorReading]:
        """
        Generate one cycle of sensor readings for all sensors.
        
        Returns:
            List of SensorReading objects, one per sensor
        """
        readings = []
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        for sensor_name, baseline in self.baselines.items():
            value = self.get_sensor_value(sensor_name)
            unit = self._get_unit(sensor_name)
            
            readings.append(SensorReading(
                equipment_id=self.equipment_id,
                timestamp=timestamp,
                sensor_name=sensor_name,
                value=value,
                unit=unit
            ))
        
        self.cycle_count += 1
        return readings
    
    @staticmethod
    def _get_unit(sensor_name: str) -> str:
        """Get engineering unit for sensor."""
        units = {
            'temperature_C': '°C',
            'vibration_mm_s': 'mm/s',
            'hydraulic_pressure_bar': 'bar',
            'rpm': 'RPM',
            'fuel_consumption_L_hr': 'L/hr',
        }
        return units.get(sensor_name, '?')
