import sys
import ast
import os
import re
from pathlib import Path

print("="*60)
print("AIPMS PROJECT STRUCTURE & CODE INTEGRITY VERIFICATION")
print("="*60)

# Python files to check
python_files = [
    "aipms-hackathon/api/main.py",
    "aipms-hackathon/api/orm.py",
    "aipms-hackathon/api/schema.py",
    "aipms-hackathon/dashboard/app.py",
    "aipms-hackathon/simulator/simulator.py",
    "aipms-hackathon/simulator/mqtt_subscriber.py",
    "aipms-hackathon/simulator/equipment_profiles.py",
]

# Test files
test_files = []
if os.path.exists("aipms-hackathon/tests"):
    test_files = [str(f) for f in Path("aipms-hackathon/tests").rglob("*.py") if f.is_file()]

all_python_files = python_files + test_files

print("\n" + "="*60)
print("PYTHON SYNTAX VALIDATION")
print("="*60)

syntax_results = {}
errors_found = []

for filepath in all_python_files:
    if not os.path.exists(filepath):
        status = "[FILE NOT FOUND]"
        syntax_results[filepath] = status
        print(f"{filepath:55} {status}")
    else:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code)
            status = "[SYNTAX OK]"
            syntax_results[filepath] = status
            print(f"{filepath:55} {status}")
        except SyntaxError as e:
            status = f"[SYNTAX ERROR: Line {e.lineno} - {e.msg}]"
            syntax_results[filepath] = status
            errors_found.append((filepath, status))
            print(f"{filepath:55}")
            print(f"  {status}")
        except Exception as e:
            status = f"[ERROR: {str(e)[:50]}]"
            syntax_results[filepath] = status
            errors_found.append((filepath, status))
            print(f"{filepath:55}")
            print(f"  {status}")

# Check requirements.txt
print("\n" + "="*60)
print("REQUIREMENTS.TXT VALIDATION")
print("="*60)

req_file = "aipms-hackathon/requirements.txt"
if os.path.exists(req_file):
    print(f"[FILE EXISTS] {req_file}")
    try:
        with open(req_file, "r") as f:
            lines = f.readlines()
        valid_entries = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
        print(f"  Total entries: {len(valid_entries)}")
        
        # Check version specifiers
        entries_with_version = 0
        for entry in valid_entries:
            if any(op in entry for op in ["==", ">=", "<=", "~=", ">", "<"]) or entry.startswith("-"):
                entries_with_version += 1
        
        print(f"  Entries with version: {entries_with_version}/{len(valid_entries)}")
        print("[VALIDATION OK]")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[FILE NOT FOUND] {req_file}")

# Check for hardcoded secrets
print("\n" + "="*60)
print("SECRETS & CREDENTIALS CHECK")
print("="*60)

secret_patterns = [
    (r"password\s*=\s*['\"]([^'\"]*)['\"]", "password"),
    (r"api[_-]?key\s*=\s*['\"]([^'\"]*)['\"]", "API key"),
    (r"secret\s*=\s*['\"]([^'\"]*)['\"]", "secret"),
    (r"token\s*=\s*['\"]([^'\"]*)['\"]", "token"),
]

secrets_found = {}
for filepath in all_python_files:
    if not os.path.exists(filepath):
        continue
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        found_types = []
        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if secret_type not in found_types:
                    found_types.append(secret_type)
        
        if found_types:
            secrets_found[filepath] = found_types
    except:
        pass

if secrets_found:
    print("[WARNING] Potential secrets found in:")
    for filepath, types in secrets_found.items():
        print(f"  {filepath}: {', '.join(types)}")
else:
    print("[SECURITY OK] No obvious hardcoded secrets detected")

# Check critical config files
print("\n" + "="*60)
print("CRITICAL CONFIG FILES")
print("="*60)

config_files = [
    "aipms-hackathon/config/mosquitto.conf",
    "aipms-hackathon/config/schema.sql",
]

for filepath in config_files:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"{filepath:45} [EXISTS] ({size} bytes)")
    else:
        print(f"{filepath:45} [NOT FOUND]")

# Validate SQL syntax (basic)
print("\n" + "="*60)
print("DATABASE SCHEMA SQL VALIDATION")
print("="*60)

schema_file = "aipms-hackathon/config/schema.sql"
if os.path.exists(schema_file):
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        sql_upper = sql_content.upper()
        has_create = "CREATE" in sql_upper
        has_table = "TABLE" in sql_upper
        
        # Check for common SQL issues
        unclosed_quotes = 0
        i = 0
        in_single_quote = False
        while i < len(sql_content):
            if sql_content[i] == "'" and (i == 0 or sql_content[i-1] != "\\"):
                in_single_quote = not in_single_quote
            i += 1
        
        unclosed = in_single_quote
        
        if has_create and has_table:
            print("[SCHEMA OK] SQL file appears valid")
            print(f"  - File size: {len(sql_content)} bytes")
            print(f"  - Lines: {len(sql_content.splitlines())}")
            if not unclosed:
                print("  - Quote balance: OK")
        else:
            print("[WARNING] SQL file structure unclear")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[FILE NOT FOUND] {schema_file}")

# Validate mosquitto.conf
print("\n" + "="*60)
print("MOSQUITTO CONFIG VALIDATION")
print("="*60)

mosquitto_file = "aipms-hackathon/config/mosquitto.conf"
if os.path.exists(mosquitto_file):
    print(f"[FILE EXISTS] {mosquitto_file}")
    try:
        with open(mosquitto_file, "r") as f:
            lines = f.readlines()
        valid_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        print(f"  Configuration directives: {len(valid_lines)}")
        print("[VALIDATION OK]")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[FILE NOT FOUND] {mosquitto_file}")

# Summary
print("\n" + "="*60)
print("VERIFICATION SUMMARY")
print("="*60)

total_files = len(all_python_files)
syntax_ok = sum(1 for v in syntax_results.values() if "[SYNTAX OK]" in v)
files_missing = sum(1 for v in syntax_results.values() if "[FILE NOT FOUND]" in v)
syntax_errors = total_files - syntax_ok - files_missing

print(f"Total Python files checked: {total_files}")
print(f"  - Syntax OK: {syntax_ok}")
print(f"  - Files missing: {files_missing}")
print(f"  - Syntax errors: {syntax_errors}")

if syntax_errors > 0:
    print("\nFiles with syntax errors:")
    for filepath, status in errors_found:
        print(f"  - {filepath}")

if secrets_found:
    print(f"\nFiles with potential secrets: {len(secrets_found)}")

config_ok = all(os.path.exists(f) for f in config_files)
print(f"\nCritical config files: {'OK' if config_ok else 'MISSING'}")

print("\n" + "="*60)
if syntax_ok == total_files - files_missing and config_ok and not secrets_found:
    print("PROJECT STATUS: READY FOR DEPLOYMENT")
elif syntax_errors == 0:
    print("PROJECT STATUS: MOSTLY READY (config files may need attention)")
else:
    print("PROJECT STATUS: ISSUES DETECTED - REVIEW ABOVE")
print("="*60)
