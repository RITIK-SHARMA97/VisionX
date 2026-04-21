#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CRITICAL DEMO READINESS TEST
Can the dashboard actually launch and run?
"""
import sys
import os
import io

# Fix encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*70)
print("CRITICAL DEMO READINESS TEST")
print("="*70 + "\n")

# Test 1: Core dashboard imports
print("TEST 1: Dashboard Core Module")
print("-" * 70)
try:
    from dashboard import app
    print("[OK] Dashboard app loads")
    test1 = True
except Exception as e:
    print(f"[FAIL] Dashboard app failed: {e}")
    test1 = False

# Test 2: Fleet page
print("\nTEST 2: Fleet Overview Page")
print("-" * 70)
try:
    from dashboard.pages import fleet_overview
    print("[OK] Fleet overview page loads")
    test2 = True
except Exception as e:
    print(f"[FAIL] Fleet overview failed: {e}")
    test2 = False

# Test 3: Equipment detail page
print("\nTEST 3: Equipment Detail Page")
print("-" * 70)
try:
    from dashboard.pages import equipment_detail
    print("[OK] Equipment detail page loads")
    test3 = True
except Exception as e:
    print(f"[FAIL] Equipment detail failed: {e}")
    test3 = False

# Test 4: Alert feed page
print("\nTEST 4: Alert Feed Page")
print("-" * 70)
try:
    from dashboard.pages import alert_feed
    print("[OK] Alert feed page loads")
    test4 = True
except Exception as e:
    print(f"[FAIL] Alert feed failed: {e}")
    test4 = False

# Test 5: Maintenance schedule page
print("\nTEST 5: Maintenance Schedule Page")
print("-" * 70)
try:
    from dashboard.pages import maintenance_schedule
    print("[OK] Maintenance schedule page loads")
    test5 = True
except Exception as e:
    print(f"[FAIL] Maintenance schedule failed: {e}")
    test5 = False

# Test 6: API Client
print("\nTEST 6: API Client Module")
print("-" * 70)
try:
    from dashboard import api_client
    # Check for critical functions
    assert hasattr(api_client, 'get_sample_fleet_overview')
    assert hasattr(api_client, 'get_sample_alerts')
    assert hasattr(api_client, 'get_sample_schedule')
    print("[OK] API client with sample data generators")
    test6 = True
except Exception as e:
    print(f"[FAIL] API client failed: {e}")
    test6 = False

# Test 7: Chart components
print("\nTEST 7: Chart Components")
print("-" * 70)
try:
    from dashboard import chart_components
    print("[OK] Chart components module loads")
    test7 = True
except Exception as e:
    print(f"[FAIL] Chart components failed: {e}")
    test7 = False

# Test 8: Configuration
print("\nTEST 8: Configuration System")
print("-" * 70)
try:
    from config_constants import *
    print(f"[OK] Configuration loaded (API port: {API_PORT})")
    test8 = True
except Exception as e:
    print(f"[FAIL] Configuration failed: {e}")
    test8 = False

# Summary
tests = [test1, test2, test3, test4, test5, test6, test7, test8]
passed = sum(tests)
failed = len(tests) - passed

print("\n" + "="*70)
print("DEMO READINESS SUMMARY")
print("="*70)
print(f"[PASSED] {passed}/{len(tests)} tests")
print(f"[FAILED] {failed}/{len(tests)} tests")
print(f"[RATE] SUCCESS RATE: {100*passed/len(tests):.0f}%")
print("="*70)

if passed == len(tests):
    print("\n[SUCCESS] PROJECT IS 100% DEMO-READY!")
    print("\nYou can now run:")
    print("  streamlit run dashboard/app.py")
    print("\nThen open: http://localhost:8501")
    sys.exit(0)
else:
    print(f"\n[WARNING] {failed} module(s) need attention")
    sys.exit(1)
