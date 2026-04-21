import sys
import warnings
import io
from contextlib import redirect_stdout, redirect_stderr

warnings.filterwarnings('ignore')
sys.path.insert(0, '.')

tests = [
    ('Streamlit Import', lambda: __import__('streamlit')),
    ('Dashboard App', lambda: __import__('dashboard.app', fromlist=['app'])),
    ('API Client', lambda: __import__('dashboard.api_client', fromlist=['api_client'])),
    ('Chart Components', lambda: __import__('dashboard.chart_components', fromlist=['chart_components'])),
    ('ORM Models', lambda: __import__('api.orm', fromlist=['orm'])),
    ('Pydantic Schemas', lambda: __import__('api.schema', fromlist=['schema'])),
    ('Config', lambda: __import__('config_constants', fromlist=['config_constants'])),
    ('Sample Fleet Data', lambda: __import__('dashboard.api_client').get_sample_fleet_overview()),
]

print('INTEGRATION TEST RESULTS')
print('=' * 60)

passed = 0
failed = 0

for test_name, test_func in tests:
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = test_func()
        print(f'PASS: {test_name}')
        passed += 1
    except Exception as e:
        print(f'FAIL: {test_name}: {str(e)[:80]}')
        failed += 1

total = passed + failed
pct = 100*passed/total if total > 0 else 0
print('=' * 60)
print(f'Summary: {passed} passed, {failed} failed ({pct:.0f}% success)')
