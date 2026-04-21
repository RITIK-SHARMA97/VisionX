#!/usr/bin/env python3
"""
Comprehensive verification script for Phase 2 refactoring.
Tests all module imports and config constant usage.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_constants():
    """Test config constants module."""
    print("\n" + "="*70)
    print("Testing config_constants.py")
    print("="*70)
    
    try:
        import config_constants as cfg
        print("✓ config_constants imported successfully")
        
        # Test MQTT constants
        assert hasattr(cfg, 'MQTT_BROKER_HOST'), "Missing MQTT_BROKER_HOST"
        assert hasattr(cfg, 'MQTT_BROKER_PORT'), "Missing MQTT_BROKER_PORT"
        assert hasattr(cfg, 'MQTT_PUBLISH_QOS'), "Missing MQTT_PUBLISH_QOS"
        print("✓ MQTT constants present")
        
        # Test Feature constants
        assert hasattr(cfg, 'FEATURE_WINDOW_SIZE'), "Missing FEATURE_WINDOW_SIZE"
        assert cfg.FEATURE_WINDOW_SIZE == 5, f"Expected FEATURE_WINDOW_SIZE=5, got {cfg.FEATURE_WINDOW_SIZE}"
        print("✓ Feature constants present")
        
        # Test Model constants
        assert hasattr(cfg, 'ANOMALY_CONTAMINATION_RATE'), "Missing ANOMALY_CONTAMINATION_RATE"
        assert hasattr(cfg, 'RUL_CLIPPING_MAX'), "Missing RUL_CLIPPING_MAX"
        assert hasattr(cfg, 'TRAINING_EPOCHS'), "Missing TRAINING_EPOCHS"
        print("✓ Model training constants present")
        
        # Test Logging constants
        assert hasattr(cfg, 'LOG_LEVEL'), "Missing LOG_LEVEL"
        assert hasattr(cfg, 'LOG_FORMAT'), "Missing LOG_FORMAT"
        print("✓ Logging constants present")
        
        return True
    except Exception as e:
        print(f"✗ config_constants test failed: {e}")
        return False


def test_api_imports():
    """Test API module imports."""
    print("\n" + "="*70)
    print("Testing API modules")
    print("="*70)
    
    try:
        from api.main import app
        print("✓ api.main imported successfully")
        
        from api.routes import equipment, alerts
        print("✓ api.routes modules imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ API import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulator_imports():
    """Test simulator module imports."""
    print("\n" + "="*70)
    print("Testing Simulator modules")
    print("="*70)
    
    try:
        from simulator.simulator import SensorSimulator
        print("✓ simulator.simulator.SensorSimulator imported successfully")
        
        from simulator.equipment_profiles import EquipmentProfile
        print("✓ simulator.equipment_profiles.EquipmentProfile imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Simulator import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_syntax():
    """Test dashboard syntax (can't fully import due to Streamlit context)."""
    print("\n" + "="*70)
    print("Testing Dashboard syntax")
    print("="*70)
    
    try:
        import py_compile
        dashboard_path = project_root / "dashboard" / "app.py"
        py_compile.compile(str(dashboard_path), doraise=True)
        print("✓ dashboard.app.py syntax valid")
        
        return True
    except Exception as e:
        print(f"✗ Dashboard syntax check failed: {e}")
        return False


def test_models_imports():
    """Test model training module imports."""
    print("\n" + "="*70)
    print("Testing Model training modules")
    print("="*70)
    
    try:
        from models.train.feature_engineer import RULScaler
        print("✓ models.train.feature_engineer imported successfully")
        
        from models.train.preprocessing import load_data
        print("✓ models.train.preprocessing imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Model imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_usage():
    """Test that refactored modules use config constants."""
    print("\n" + "="*70)
    print("Testing config usage in refactored modules")
    print("="*70)
    
    try:
        import config_constants as cfg
        from simulator.simulator import SensorSimulator
        
        # Create a simulator instance to verify it uses config defaults
        sim = SensorSimulator('TEST-01', 'healthy')
        
        # Verify defaults come from config
        assert sim.broker_host == cfg.MQTT_BROKER_HOST, "Simulator should use cfg.MQTT_BROKER_HOST"
        assert sim.broker_port == cfg.MQTT_BROKER_PORT, "Simulator should use cfg.MQTT_BROKER_PORT"
        print(f"✓ SensorSimulator uses config defaults: host={sim.broker_host}, port={sim.broker_port}")
        
        # Test feature engineer uses config
        from models.train.feature_engineer import RULScaler
        scaler = RULScaler()
        assert scaler.rul_max == cfg.RUL_CLIPPING_MAX, "RULScaler should use cfg.RUL_CLIPPING_MAX"
        print(f"✓ RULScaler uses config constant: rul_max={scaler.rul_max}")
        
        return True
    except Exception as e:
        print(f"✗ Config usage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("▶" * 35)
    print("AIPMS Phase 2 Refactoring Verification")
    print("▶" * 35)
    
    results = {
        "Config Constants": test_config_constants(),
        "API Modules": test_api_imports(),
        "Simulator Modules": test_simulator_imports(),
        "Dashboard Syntax": test_dashboard_syntax(),
        "Model Training Modules": test_models_imports(),
        "Config Usage": test_config_usage(),
    }
    
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    all_passed = all(results.values())
    
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Refactoring Phase 2 complete!")
        print("="*70)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Review errors above")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
