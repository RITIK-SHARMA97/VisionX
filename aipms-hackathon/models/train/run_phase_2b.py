"""
Phase 2B Master Training Script
Orchestrates entire ML data preparation and model training pipeline

This script runs all Phase 2B stages:
1. Data download verification
2. Data preprocessing & feature engineering
3. Anomaly detection model training (Isolation Forest)
4. Failure prediction model training (XGBoost)
5. RUL estimation model training (LSTM)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.abspath('../..')
os.chdir(project_root)

print("=" * 100)
print(" " * 20 + "PHASE 2B: ML DATA PREPARATION & MODEL TRAINING")
print("=" * 100)

print(f"\nProject root: {os.getcwd()}")
print(f"Date/Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Define phases
phases = [
    {
        'name': '2B.1 - Data Download Verification',
        'script': 'models/train/00_download.py',
        'duration': '5 min'
    },
    {
        'name': '2B.2 - Data Preprocessing & Feature Engineering',
        'script': 'models/train/01_preprocess.py',
        'duration': '10 min'
    },
    {
        'name': '2B.3 - Anomaly Detection (Isolation Forest)',
        'script': 'models/train/02_train_anomaly.py',
        'duration': '5 min'
    },
    {
        'name': '2B.4 - Failure Prediction (XGBoost)',
        'script': 'models/train/02_train_failure.py',
        'duration': '15 min'
    },
    {
        'name': '2B.5 - RUL Estimation (LSTM)',
        'script': 'models/train/03_train_rul.py',
        'duration': '20 min'
    }
]

print(f"\n{'Phase':<50} {'Duration':<15} {'Status'}")
print("-" * 80)
for phase in phases:
    print(f"{phase['name']:<50} {phase['duration']:<15} {'Queued'}")

# Verify prerequisites
print(f"\n{'=' * 100}")
print("PREREQUISITES CHECK")
print(f"{'=' * 100}")

# Check Python packages
required_packages = {
    'numpy': 'Numerical computing',
    'pandas': 'Data manipulation',
    'sklearn': 'Machine learning',
    'xgboost': 'XGBoost models',
    'torch': 'PyTorch (LSTM)',
    'matplotlib': 'Plotting (optional)',
    'shap': 'SHAP explainability (optional)'
}

missing_packages = []
print("\nChecking Python packages:")

for pkg, desc in required_packages.items():
    try:
        __import__(pkg)
        print(f"  [OK] {pkg:<15} {desc}")
    except ImportError:
        print(f"  [MISSING] {pkg:<15} {desc}")
        missing_packages.append(pkg)

if missing_packages:
    print(f"\n[ERROR] Missing packages detected: {', '.join(missing_packages)}")
    print(f"Install with: pip install {' '.join(missing_packages)}")
    sys.exit(1)

# Check data directories
print(f"\nChecking directories:")
dirs_to_create = ['data/raw', 'data/processed', 'data/scalers', 'models/saved']
for d in dirs_to_create:
    Path(d).mkdir(parents=True, exist_ok=True)
    print(f"  [OK] {d}")

# Check C-MAPSS data
print(f"\nChecking data files:")
required_files = [
    'data/raw/train_FD001.txt',
    'data/raw/test_FD001.txt',
    'data/raw/RUL_FD001.txt',
    'data/raw/train_FD003.txt',
    'data/raw/test_FD003.txt',
    'data/raw/RUL_FD003.txt'
]

missing_files = [f for f in required_files if not os.path.exists(f)]
if missing_files:
    print(f"  ⚠ Missing C-MAPSS data files:")
    for f in missing_files:
        print(f"    • {f}")
    print(f"\n  Download from: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps")
    print(f"  Then re-run this script.")
else:
    print(f"  [OK] All data files present")

# Run phases
print(f"\n{'=' * 100}")
print("EXECUTION")
print(f"{'=' * 100}")

completed = []
failed = []

for i, phase in enumerate(phases, 1):
    print(f"\n[{i}/{len(phases)}] {phase['name']}")
    print("-" * 100)
    
    try:
        result = subprocess.run(
            [sys.executable, phase['script']],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per phase
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n[OK] {phase['name']} PASSED")
            completed.append(phase['name'])
        else:
            print(f"\n[FAILED] {phase['name']} FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            failed.append(phase['name'])
    
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {phase['name']} TIMEOUT (>5 min)")
        failed.append(phase['name'])
    except Exception as e:
        print(f"[ERROR] {phase['name']} ERROR: {e}")
        failed.append(phase['name'])

# Summary
print(f"\n{'=' * 100}")
print("SUMMARY")
print(f"{'=' * 100}")

print(f"\n[OK] Completed: {len(completed)}/{len(phases)}")
for phase in completed:
    print(f"  [OK] {phase}")

if failed:
    print(f"\n[FAILED] Failed: {len(failed)}/{len(phases)}")
    for phase in failed:
        print(f"  [ERROR] {phase}")

# Verify outputs
print(f"\n{'=' * 100}")
print("OUTPUT VERIFICATION")
print(f"{'=' * 100}")

expected_outputs = {
    'data/processed/FD001_X.npy': 'FD001 features',
    'data/processed/FD001_y.npy': 'FD001 labels',
    'data/processed/FD001_rul.npy': 'FD001 RUL',
    'data/scalers/scaler.pkl': 'Feature scaler',
    'models/saved/anomaly_detector_v1.pkl': 'Anomaly model',
    'models/saved/failure_predictor_v1.pkl': 'Failure model',
    'models/saved/rul_estimator_v1.pt': 'RUL model'
}

print(f"\nChecking outputs:")
all_outputs_present = True
for path, desc in expected_outputs.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        size_str = f"{size / (1024**2):.2f} MB" if size > 1024**2 else f"{size / 1024:.2f} KB"
        print(f"  [OK] {path:<45} ({size_str})")
    else:
        print(f"  [MISSING] {path:<45} MISSING")
        all_outputs_present = False

# Final status
print(f"\n{'=' * 100}")
if len(failed) == 0 and all_outputs_present:
    print("[OK] PHASE 2B COMPLETE - All stages passed!")
    print("=" * 100)
    print("\nNext steps:")
    print("  1. Run Phase 3A (API Backend Deployment): python api/main.py")
    print("  2. Run Phase 3B (Dashboard): streamlit run dashboard/app.py")
    print("  3. Run Phase 3C (Full System Test): python tests/test_e2e.py")
    exit(0)
else:
    print("[FAILED] PHASE 2B INCOMPLETE - Some stages failed or outputs missing")
    print("=" * 100)
    print("\nTroubleshooting:")
    print("  1. Check that all required packages are installed")
    print("  2. Verify C-MAPSS data is in data/raw/")
    print("  3. Check disk space (≥500 MB recommended)")
    print("  4. Review error messages above")
    exit(1)
