"""
Phase 2B.1: Download C-MAPSS Dataset
NASA Turbofan Engine Degradation Dataset
Public domain - https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6

Downloads FD001 and FD003 subsets for training and validation.
"""

import os
import urllib.request
import urllib.error
import time
from pathlib import Path

# Create data directory
os.makedirs('data/raw', exist_ok=True)

# NASA C-MAPSS dataset URLs (space-separated format, no CSV)
datasets = {
    'FD001_train': 'https://www.kaggle.com/api/v1/datasets/download/behrad3d/nasa-cmaps',
    'FD003_train': 'https://www.kaggle.com/api/v1/datasets/download/behrad3d/nasa-cmaps'
}

# Alternative: Direct public links (may require authentication)
kaggle_datasets = {
    'FD001': {
        'train': 'train_FD001.txt',
        'test': 'test_FD001.txt',
        'rul': 'RUL_FD001.txt'
    },
    'FD003': {
        'train': 'train_FD003.txt',
        'test': 'test_FD003.txt',
        'rul': 'RUL_FD003.txt'
    }
}

print("=" * 80)
print("C-MAPSS Dataset Download Utility")
print("=" * 80)
print("\nOPTION 1: Using Kaggle CLI (Recommended)")
print("-" * 80)
print("If you have Kaggle credentials configured:")
print("  1. Install: pip install kaggle")
print("  2. Configure: Place kaggle.json in ~/.kaggle/")
print("  3. Run: kaggle datasets download -d behrad3d/nasa-cmaps --unzip --path data/raw")
print("\nOPTION 2: Manual Download")
print("-" * 80)
print("Download from: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps")
print("Extract to: data/raw/")
print("Verify files: train_FD001.txt, test_FD001.txt, RUL_FD001.txt")
print("             train_FD003.txt, test_FD003.txt, RUL_FD003.txt")

print("\nOPTION 3: Using NASA Official Repository")
print("-" * 80)
print("Download from: https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6")
print("Format: Space-separated ASCII files")
print("Column order: engine_id, cycle, op_setting_1, op_setting_2, op_setting_3, sensor_1...sensor_21")

def verify_dataset():
    """Verify C-MAPSS files are present"""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    raw_dir = Path('data/raw')
    required_files = [
        'train_FD001.txt', 'test_FD001.txt', 'RUL_FD001.txt',
        'train_FD003.txt', 'test_FD003.txt', 'RUL_FD003.txt'
    ]
    
    found_files = []
    missing_files = []
    
    for fname in required_files:
        fpath = raw_dir / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            found_files.append(f"  [OK] {fname} ({size_mb:.2f} MB)")
        else:
            missing_files.append(f"  [MISSING] {fname}")
    
    if found_files:
        print("\n[OK] Found files:")
        for f in found_files:
            print(f)
    
    if missing_files:
        print("\n[MISSING] Missing files:")
        for f in missing_files:
            print(f)
        print("\nPlease download C-MAPSS dataset using one of the options above.")
        return False
    
    print("\n[OK] All required files present!")
    return True

if __name__ == "__main__":
    verify_dataset()
    print("\nNext step: python models/train/01_preprocess.py")
