#!/usr/bin/env python
"""Quick integration test - verify all systems work together."""
import subprocess
import time
import sys
from pathlib import Path

print("\n" + "="*70)
print("AIPMS SYSTEM INTEGRATION TEST")
print("="*70)

tests = [
    ("Database", "python -c \"import sqlite3; c=sqlite3.connect('aipms.db'); print(f'✓ {len(c.execute(\\\"SELECT name FROM sqlite_master WHERE type=table\\\").fetchall())} tables')\""),
    ("ML Models", "python -c \"from pathlib import Path; m=list(Path('models/saved').glob('*.pkl'))+list(Path('models/saved').glob('*.pt')); print(f'✓ {len(m)} models')\""),
    ("API Import", "python -c \"from api.main import app; print('✓ FastAPI initialized')\""),
    ("Simulator", "python -c \"from simulator import SensorSimulator, SimulatorEngine; print('✓ Simulator ready')\""),
    ("Dashboard", "python -c \"from dashboard.app import create_dashboard; print('✓ Dashboard importable')\""),
]

passed = 0
failed = 0

for test_name, cmd in tests:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = result.stdout.strip() or result.stderr.strip()
        if result.returncode == 0 and "✓" in output:
            print(f"  ✓ {test_name:20} {output}")
            passed += 1
        else:
            print(f"  ✗ {test_name:20} {output[:50]}")
            failed += 1
    except Exception as e:
        print(f"  ✗ {test_name:20} {str(e)[:50]}")
        failed += 1

print("\n" + "="*70)
print(f"RESULT: {passed}/{len(tests)} tests passed")
if failed == 0:
    print("✓ ALL SYSTEMS READY FOR DEMO")
else:
    print(f"✗ {failed} system(s) need attention")
print("="*70 + "\n")

sys.exit(0 if failed == 0 else 1)
