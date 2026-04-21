#!/usr/bin/env python3
"""
Dashboard Verification Script
Checks that dashboard/app.py has valid syntax and required dependencies.
"""

import sys
import ast

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "✅ Syntax valid"
    except SyntaxError as e:
        return False, f"❌ Syntax error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def check_imports():
    """Check if required packages are available."""
    required_packages = {
        'streamlit': 'Streamlit framework',
        'requests': 'HTTP client',
        'logging': 'Python logging',
        'datetime': 'Datetime utilities',
        'typing': 'Type hints',
    }
    
    print("\n═══════════════════════════════════════")
    print("DEPENDENCY CHECK")
    print("═══════════════════════════════════════")
    
    all_available = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package:20} - {description}")
        except ImportError:
            print(f"❌ {package:20} - NOT INSTALLED")
            all_available = False
    
    return all_available

def main():
    print("\n═══════════════════════════════════════")
    print("AIPMS DASHBOARD VERIFICATION")
    print("═══════════════════════════════════════")
    
    # Check syntax
    print("\nChecking dashboard/app.py syntax...")
    app_path = "aipms-hackathon/dashboard/app.py"
    valid, msg = check_syntax(app_path)
    print(f"  {msg}")
    
    if not valid:
        print("\n❌ Dashboard has syntax errors. Please fix before running.")
        return False
    
    # Check imports
    all_deps = check_imports()
    
    print("\n═══════════════════════════════════════")
    print("LAUNCH INSTRUCTIONS")
    print("═══════════════════════════════════════")
    print("""
To start the dashboard:

  1. Ensure FastAPI backend is running (on port 8000):
     cd aipms-hackathon
     python api/main.py
  
  2. In a new terminal, start the Streamlit dashboard:
     cd aipms-hackathon
     streamlit run dashboard/app.py
  
  3. Browser will open to: http://localhost:8501

Expected behavior:
  - Page loads with "AIPMS Dashboard" title
  - Sidebar shows navigation: Fleet Overview, Equipment Detail, Schedule, Alert Feed
  - API health check shows ✅ or ❌
  - Fleet Overview loads equipment cards
  - Navigation between screens works
  - Auto-refresh happens every 5 seconds
""")
    
    print("\n═══════════════════════════════════════")
    if valid and all_deps:
        print("✅ READY TO LAUNCH")
        print("═══════════════════════════════════════")
        return True
    else:
        print("⚠️  ISSUES DETECTED")
        print("═══════════════════════════════════════")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
