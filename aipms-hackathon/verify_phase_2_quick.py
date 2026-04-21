#!/usr/bin/env python3
"""Quick verification of Phase 2 refactoring completion."""

import sys

print("\n" + "="*70)
print("PHASE 2 REFACTORING VERIFICATION")
print("="*70)

# Test 1: Config Constants
try:
    import config_constants as cfg
    assert hasattr(cfg, 'MQTT_BROKER_HOST')
    assert hasattr(cfg, 'TRAINING_EPOCHS')
    assert hasattr(cfg, 'TRAINING_BATCH_SIZE')
    assert hasattr(cfg, 'TRAINING_LEARNING_RATE')
    print("✓ Config constants OK (includes new training constants)")
except Exception as e:
    print(f"✗ Config constants FAILED: {e}")
    sys.exit(1)

# Test 2: Simulator
try:
    from simulator.simulator import SensorSimulator
    sim = SensorSimulator('TEST-01', 'healthy')
    assert sim.broker_host == cfg.MQTT_BROKER_HOST
    assert sim.broker_port == cfg.MQTT_BROKER_PORT
    print(f"✓ Simulator OK (uses cfg defaults: {sim.broker_host}:{sim.broker_port})")
except Exception as e:
    print(f"✗ Simulator FAILED: {e}")
    sys.exit(1)

# Test 3: Dashboard syntax
try:
    import py_compile
    py_compile.compile("dashboard/app.py", doraise=True)
    print("✓ Dashboard syntax OK")
except Exception as e:
    print(f"✗ Dashboard FAILED: {e}")
    sys.exit(1)

# Test 4: Feature Engineer  
try:
    from models.train.feature_engineer import RULScaler
    scaler = RULScaler()
    assert scaler.rul_max == cfg.RUL_CLIPPING_MAX
    print(f"✓ Feature Engineer OK (rul_max={scaler.rul_max})")
except Exception as e:
    print(f"✗ Feature Engineer FAILED: {e}")
    sys.exit(1)

# Test 5: Preprocessing imports
try:
    import models.train.preprocess
    print("✓ Preprocess module OK")
except Exception as e:
    print(f"✗ Preprocess FAILED: {e}")
    sys.exit(1)

# Test 6: Model training files syntax
try:
    import py_compile
    files = [
        "models/train/02_train_anomaly.py",
        "models/train/02_train_failure.py",
        "models/train/03_train_rul.py"
    ]
    for f in files:
        py_compile.compile(f, doraise=True)
    print("✓ Model training files syntax OK")
except Exception as e:
    print(f"✗ Model training files FAILED: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✓ PHASE 2 REFACTORING COMPLETE AND VERIFIED")
print("="*70 + "\n")
