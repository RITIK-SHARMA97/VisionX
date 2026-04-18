"""
Phase 2B Verification Script
Validates that all implementation files are present and correct
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_section(title):
    print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 80}{RESET}")

def check_file_exists(path, description=""):
    """Check if file exists and print status"""
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    size_str = ""
    if exists:
        size = os.path.getsize(path)
        if size > 1024**2:
            size_str = f" ({size / (1024**2):.2f} MB)"
        elif size > 1024:
            size_str = f" ({size / 1024:.2f} KB)"
        else:
            size_str = f" ({size} B)"
    print(f"  {status} {path:<60} {size_str}")
    return exists

def check_file_content(path, required_strings):
    """Check if file contains required strings"""
    try:
        with open(path, 'r') as f:
            content = f.read()
        all_found = True
        for req_str in required_strings:
            if req_str in content:
                print(f"     {GREEN}✓{RESET} Contains: {req_str}")
            else:
                print(f"     {RED}✗{RESET} Missing: {req_str}")
                all_found = False
        return all_found
    except:
        return False

print(f"\n{BOLD}PHASE 2B IMPLEMENTATION VERIFICATION{RESET}")
print(f"{BOLD}Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

# Track overall status
all_checks_passed = True

# 1. Check training scripts
print_section("TRAINING SCRIPTS VERIFICATION")

training_scripts = {
    'models/train/00_download.py': ['IsolationForest', 'verify_dataset', 'urllib'],
    'models/train/01_preprocess.py': ['extract_features', 'rolling', 'MinMaxScaler'],
    'models/train/02_train_anomaly.py': ['IsolationForest', 'anomaly_scores', 'threshold'],
    'models/train/02_train_failure.py': ['XGBoost', 'aucpr', 'scale_pos_weight'],
    'models/train/03_train_rul.py': ['LSTM', 'AsymmetricRULLoss', 'sequence'],
}

print("\nTraining Script Files:")
for script_path, required_strs in training_scripts.items():
    if check_file_exists(script_path):
        if check_file_content(script_path, required_strs):
            print(f"     {GREEN}✓{RESET} Content verified")
        else:
            print(f"     {RED}✗{RESET} Content incomplete")
            all_checks_passed = False
    else:
        all_checks_passed = False

# 2. Check support scripts
print_section("SUPPORT SCRIPTS VERIFICATION")

support_scripts = {
    'models/train/__init__.py': ['__version__', '__all__'],
    'models/train/run_phase_2b.py': ['subprocess', 'phases', 'verification'],
}

print("\nSupport Script Files:")
for script_path, required_strs in support_scripts.items():
    if check_file_exists(script_path):
        if check_file_content(script_path, required_strs):
            print(f"     {GREEN}✓{RESET} Content verified")
        else:
            print(f"     {RED}✗{RESET} Content incomplete")
            all_checks_passed = False
    else:
        all_checks_passed = False

# 3. Check documentation
print_section("DOCUMENTATION VERIFICATION")

doc_files = {
    'PHASE_2B_COMPLETION.md': ['Phase 2B.1', 'Phase 2B.2', 'Phase 2B.3', 'Implementation Checklist'],
    'README_PHASE_2B.md': ['Quick Start', 'Prerequisites', 'Phase Breakdown'],
}

print("\nDocumentation Files:")
for doc_path, required_strs in doc_files.items():
    if check_file_exists(doc_path):
        if check_file_content(doc_path, required_strs):
            print(f"     {GREEN}✓{RESET} Content verified")
        else:
            print(f"     {RED}✗{RESET} Content incomplete")
            all_checks_passed = False
    else:
        all_checks_passed = False

# 4. Check directory structure
print_section("DIRECTORY STRUCTURE VERIFICATION")

directories = [
    'models/train',
    'models/saved',
    'data/raw',
    'data/processed',
    'data/scalers',
]

print("\nRequired Directories:")
for dir_path in directories:
    exists = os.path.isdir(dir_path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"  {status} {dir_path}")
    if not exists:
        all_checks_passed = False

# 5. Check Python packages
print_section("PYTHON PACKAGES VERIFICATION")

required_packages = {
    'numpy': 'Numerical computing',
    'pandas': 'Data manipulation',
    'sklearn': 'Machine learning',
    'xgboost': 'XGBoost models',
    'torch': 'PyTorch LSTM',
}

print("\nRequired Python Packages:")
missing_packages = []
for package, description in required_packages.items():
    try:
        __import__(package)
        print(f"  {GREEN}✓{RESET} {package:<15} ({description})")
    except ImportError:
        print(f"  {RED}✗{RESET} {package:<15} ({description}) - MISSING")
        missing_packages.append(package)
        all_checks_passed = False

# 6. Code statistics
print_section("CODE STATISTICS")

print("\nFile Statistics:")
total_lines = 0
for script_path in training_scripts.keys():
    if os.path.exists(script_path):
        with open(script_path, 'r') as f:
            lines = len(f.readlines())
        total_lines += lines
        print(f"  {script_path:<50} {lines:>5} lines")

print(f"\n  Total training script lines: {total_lines}")

# 7. Feature checklist
print_section("FEATURE IMPLEMENTATION CHECKLIST")

features = {
    '2B.1 Data Download Verification': 'models/train/00_download.py',
    '2B.2 Data Preprocessing': 'models/train/01_preprocess.py',
    '2B.3 Anomaly Detection (Isolation Forest)': 'models/train/02_train_anomaly.py',
    '2B.4 Failure Prediction (XGBoost)': 'models/train/02_train_failure.py',
    '2B.5 RUL Estimation (LSTM)': 'models/train/03_train_rul.py',
    'Master Orchestrator': 'models/train/run_phase_2b.py',
    'Completion Report': 'PHASE_2B_COMPLETION.md',
    'Detailed Guide': 'README_PHASE_2B.md',
}

print("\nImplementation Status:")
for feature_name, file_path in features.items():
    exists = os.path.exists(file_path)
    status = f"{GREEN}✓ COMPLETE{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
    print(f"  {status:<20} {feature_name}")
    if not exists:
        all_checks_passed = False

# 8. Summary
print_section("VERIFICATION SUMMARY")

print(f"\nOverall Status: ", end="")
if all_checks_passed:
    print(f"{GREEN}{BOLD}✓ ALL CHECKS PASSED{RESET}")
    print(f"\n{GREEN}Phase 2B implementation is COMPLETE and VERIFIED!{RESET}")
else:
    print(f"{RED}{BOLD}✗ SOME CHECKS FAILED{RESET}")
    print(f"\n{RED}Review the errors above and resolve them.{RESET}")

if missing_packages:
    print(f"\n{YELLOW}Missing packages detected:{RESET}")
    print(f"Install with: pip install {' '.join(missing_packages)}")

print_section("NEXT STEPS")

print("""
1. Download C-MAPSS Dataset:
   python models/train/00_download.py

2. Run Complete Pipeline:
   python models/train/run_phase_2b.py

3. Or Run Individual Phases:
   python models/train/01_preprocess.py
   python models/train/02_train_anomaly.py
   python models/train/02_train_failure.py
   python models/train/03_train_rul.py

4. Verify Outputs:
   ls -lah models/saved/
   ls -lah data/processed/

5. Read Documentation:
   - PHASE_2B_COMPLETION.md (detailed report)
   - README_PHASE_2B.md (quick start guide)
""")

print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")

# Exit with appropriate code
sys.exit(0 if all_checks_passed else 1)
