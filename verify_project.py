import sys
import ast
import os
import re
from pathlib import Path

print('='*60)
print('AIPMS PROJECT STRUCTURE & CODE INTEGRITY VERIFICATION')
print('='*60)

# Python files to check
python_files = [
    'aipms-hackathon/api/main.py',
    'aipms-hackathon/api/orm.py',
    'aipms-hackathon/api/schema.py',
    'aipms-hackathon/dashboard/app.py',
    'aipms-hackathon/simulator/simulator.py',
    'aipms-hackathon/simulator/mqtt_subscriber.py',
    'aipms-hackathon/simulator/equipment_profiles.py',
]

# Test files
test_files = []
if os.path.exists('tests'):
    test_files = [str(f) for f in Path('tests').rglob('*.py') if f.is_file()]

all_python_files = python_files + test_files

print('\n' + '='*60)
print('PYTHON SYNTAX VALIDATION')
print('='*60)

syntax_results = {}
for filepath in all_python_files:
    if not os.path.exists(filepath):
        status = '[FILE NOT FOUND]'
        syntax_results[filepath] = status
        print(f'{filepath:50} {status}')
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code)
            status = '[SYNTAX OK]'
            syntax_results[filepath] = status
            print(f'{filepath:50} {status}')
        except SyntaxError as e:
            status = f'[SYNTAX ERROR: Line {e.lineno} - {e.msg}]'
            syntax_results[filepath] = status
            print(f'{filepath:50}')
            print(f'  {status}')
        except Exception as e:
            status = f'[ERROR: {str(e)[:50]}]'
            syntax_results[filepath] = status
            print(f'{filepath:50}')
            print(f'  {status}')

# Check requirements.txt
print('\n' + '='*60)
print('REQUIREMENTS.TXT VALIDATION')
print('='*60)

if os.path.exists('requirements.txt'):
    print('[FILE EXISTS] requirements.txt')
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        valid_entries = [l for l in lines if l.strip() and not l.startswith('#')]
        print(f'  Entries: {len(valid_entries)}')
        print('[VALIDATION OK]')
    except Exception as e:
        print(f'[ERROR] {e}')
else:
    print('[FILE NOT FOUND] requirements.txt')

# Check for hardcoded secrets
print('\n' + '='*60)
print('SECRETS & CREDENTIALS CHECK')
print('='*60)

secret_patterns = [
    (r'password\s*=\s*["\047]([^"\047]*)["\047]', 'password'),
    (r'api[_-]?key\s*=\s*["\047]([^"\047]*)["\047]', 'API key'),
    (r'secret\s*=\s*["\047]([^"\047]*)["\047]', 'secret'),
]

secrets_found = {}
for filepath in all_python_files:
    if not os.path.exists(filepath):
        continue
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found = []
        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found.append(secret_type)
        
        if found:
            secrets_found[filepath] = found
    except:
        pass

if secrets_found:
    print('[WARNING] Potential secrets found in:')
    for filepath in secrets_found.keys():
        print(f'  - {filepath}')
else:
    print('[SECURITY OK] No obvious hardcoded secrets detected')

# Check critical config files
print('\n' + '='*60)
print('CRITICAL CONFIG FILES')
print('='*60)

config_files = [
    'config/mosquitto.conf',
    'config/schema.sql',
]

for filepath in config_files:
    if os.path.exists(filepath):
        print(f'{filepath:40} [EXISTS]')
    else:
        print(f'{filepath:40} [NOT FOUND]')

# Validate SQL syntax (basic)
print('\n' + '='*60)
print('DATABASE SCHEMA SQL VALIDATION')
print('='*60)

if os.path.exists('config/schema.sql'):
    try:
        with open('config/schema.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        sql_upper = sql_content.upper()
        has_create = 'CREATE' in sql_upper
        has_table = 'TABLE' in sql_upper
        
        if has_create and has_table:
            print('[SCHEMA OK] SQL file appears valid')
            print(f'  - File size: {len(sql_content)} bytes')
            print(f'  - Lines: {len(sql_content.splitlines())}')
        else:
            print('[SCHEMA CHECK] May contain DDL')
    except Exception as e:
        print(f'[ERROR] {e}')
else:
    print('[FILE NOT FOUND] config/schema.sql')

# Summary
print('\n' + '='*60)
print('VERIFICATION SUMMARY')
print('='*60)

total_files = len(all_python_files)
syntax_ok = sum(1 for v in syntax_results.values() if '[SYNTAX OK]' in v)
files_missing = sum(1 for v in syntax_results.values() if '[FILE NOT FOUND]' in v)

print(f'Total Python files checked: {total_files}')
print(f'  - Syntax OK: {syntax_ok}')
print(f'  - Files missing: {files_missing}')
print(f'  - Errors: {total_files - syntax_ok - files_missing}')

print('='*60)
