"""
Enhanced C-MAPSS Dataset Download Helper
Helps manage manual downloads and validates file integrity
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime

def verify_files():
    """Check for all required C-MAPSS files in data/raw"""
    raw_dir = Path('data/raw')
    
    required_files = {
        'train_FD001.txt': {'min_size_mb': 12.0, 'max_size_mb': 15.0},
        'test_FD001.txt': {'min_size_mb': 5.0, 'max_size_mb': 6.0},
        'RUL_FD001.txt': {'min_size_mb': 0.001, 'max_size_mb': 0.1},
        'train_FD003.txt': {'min_size_mb': 12.0, 'max_size_mb': 15.0},
        'test_FD003.txt': {'min_size_mb': 5.0, 'max_size_mb': 6.0},
        'RUL_FD003.txt': {'min_size_mb': 0.001, 'max_size_mb': 0.1},
    }
    
    print("=" * 80)
    print("C-MAPSS DATASET VERIFICATION")
    print("=" * 80)
    print(f"\nChecking: {raw_dir.absolute()}\n")
    
    os.makedirs(raw_dir, exist_ok=True)
    
    found_files = []
    missing_files = []
    invalid_files = []
    
    for filename, size_specs in required_files.items():
        filepath = raw_dir / filename
        
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            min_size = size_specs['min_size_mb']
            max_size = size_specs['max_size_mb']
            
            if min_size <= size_mb <= max_size:
                found_files.append({
                    'name': filename,
                    'size_mb': size_mb,
                    'status': '✓'
                })
            else:
                invalid_files.append({
                    'name': filename,
                    'size_mb': size_mb,
                    'expected': f"{min_size}-{max_size} MB",
                    'status': '⚠'
                })
        else:
            missing_files.append({'name': filename, 'status': '✗'})
    
    # Display results
    if found_files:
        print("✓ VALID FILES FOUND:")
        print("-" * 80)
        for f in found_files:
            print(f"  ✓ {f['name']:<25} {f['size_mb']:>8.2f} MB")
    
    if invalid_files:
        print("\n⚠ FILES WITH UNEXPECTED SIZE:")
        print("-" * 80)
        for f in invalid_files:
            print(f"  ⚠ {f['name']:<25} {f['size_mb']:>8.2f} MB (expected {f['expected']})")
    
    if missing_files:
        print("\n✗ MISSING FILES:")
        print("-" * 80)
        for f in missing_files:
            print(f"  ✗ {f['name']}")
    
    # Summary
    total_found = len(found_files)
    total_required = len(required_files)
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_found}/{total_required} files found")
    print("=" * 80)
    
    if total_found == total_required:
        total_size_mb = sum(f['size_mb'] for f in found_files)
        print(f"\n✓ SUCCESS! All files ready")
        print(f"  Total dataset size: {total_size_mb:.2f} MB")
        print(f"\nNext step:")
        print(f"  python models/train/run_phase_2b.py")
        return True
    else:
        print(f"\n✗ INCOMPLETE - Missing {total_required - total_found} files")
        print(f"\n📥 DOWNLOAD INSTRUCTIONS:")
        print(f"  1. Visit: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps")
        print(f"  2. Click 'Download' button")
        print(f"  3. Extract zip to: {raw_dir.absolute()}")
        print(f"  4. Run this script again to verify")
        print(f"\n📖 Detailed guide: DOWNLOAD_CMAPSS_GUIDE.md")
        return False

def check_file_format(filename, max_lines_to_check=5):
    """Verify file format is correct (space-separated values)"""
    filepath = Path('data/raw') / filename
    
    if not filepath.exists():
        return False
    
    try:
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                if i >= max_lines_to_check:
                    break
                parts = line.strip().split()
                if len(parts) < 3:
                    return False
        return True
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return False

def estimate_preprocessing_time():
    """Estimate how long preprocessing will take"""
    raw_dir = Path('data/raw')
    total_size_mb = 0
    
    for file in ['train_FD001.txt', 'train_FD003.txt', 'test_FD001.txt', 'test_FD003.txt']:
        filepath = raw_dir / file
        if filepath.exists():
            total_size_mb += filepath.stat().st_size / (1024 * 1024)
    
    # Rough estimate: ~1 MB per 10 seconds
    estimated_seconds = total_size_mb * 10
    estimated_minutes = estimated_seconds / 60
    
    return estimated_minutes

def main():
    print("\n")
    
    # Check Python version
    import sys
    if sys.version_info < (3, 8):
        print("⚠ WARNING: Python 3.8+ required")
        return
    
    # Run verification
    all_good = verify_files()
    
    if all_good:
        est_time = estimate_preprocessing_time()
        print(f"\n📊 PREPROCESSING ESTIMATE:")
        print(f"  Expected time: ~{est_time:.0f} minutes")
        print(f"\n✅ Ready to start ML pipeline!")
    else:
        print(f"\n⏸ Download required before proceeding")

if __name__ == '__main__':
    main()
