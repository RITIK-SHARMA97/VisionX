import sys
sys.path.insert(0, '.')

print('='*60)
print('IMPORT TEST RESULTS - PHASE 1 GATE')
print('='*60)
print()

results = []

# Test 1: simulator.equipment_profiles
try:
    from simulator.equipment_profiles import EquipmentProfile
    print('[PASS] simulator.equipment_profiles - EquipmentProfile')
    results.append(True)
except Exception as e:
    print(f'[FAIL] simulator.equipment_profiles: {str(e)[:50]}')
    results.append(False)

# Test 2: simulator.simulator
try:
    from simulator.simulator import SimulatorEngine
    print('[PASS] simulator.simulator - SimulatorEngine')
    results.append(True)
except Exception as e:
    print(f'[FAIL] simulator.simulator: {str(e)[:50]}')
    results.append(False)

# Test 3: simulator.mqtt_subscriber
try:
    from simulator.mqtt_subscriber import MQTTSubscriber
    print('[PASS] simulator.mqtt_subscriber - MQTTSubscriber')
    results.append(True)
except Exception as e:
    print(f'[FAIL] simulator.mqtt_subscriber: {str(e)[:50]}')
    results.append(False)

# Test 4: api.main
try:
    from api.main import app
    print('[PASS] api.main - app (FastAPI)')
    results.append(True)
except Exception as e:
    print(f'[FAIL] api.main: {str(e)[:50]}')
    results.append(False)

# Test 5: api.orm
try:
    from api.orm import Base
    print('[PASS] api.orm - Base')
    results.append(True)
except Exception as e:
    print(f'[FAIL] api.orm: {str(e)[:50]}')
    results.append(False)

# Test 6: api.schema
try:
    from api.schema import MaintenanceAlert
    print('[PASS] api.schema - MaintenanceAlert')
    results.append(True)
except Exception as e:
    print(f'[FAIL] api.schema: {str(e)[:50]}')
    results.append(False)

# Test 7: dashboard.app
try:
    from dashboard.app import create_dashboard
    print('[PASS] dashboard.app - create_dashboard')
    results.append(True)
except Exception as e:
    print(f'[FAIL] dashboard.app: {str(e)[:50]}')
    results.append(False)

print()
print('='*60)
passed = sum(results)
total = len(results)
pct = int(100*passed/total) if total > 0 else 0
print('SUMMARY: {}/{} imports successful ({}%)'.format(passed, total, pct))
print('='*60)
