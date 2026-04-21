import sys
import inspect
sys.path.insert(0, 'dashboard')

try:
    import api_client
    
    print("=" * 70)
    print("STEP 4: FUNCTION AVAILABILITY CHECK - api_client.py")
    print("=" * 70)
    
    # Get all functions in the module
    functions = inspect.getmembers(api_client, inspect.isfunction)
    
    print(f"\nTotal functions found: {len(functions)}\n")
    
    # List all functions
    print("Functions in api_client.py:")
    print("-" * 70)
    
    callable_count = 0
    for func_name, func in functions:
        if not func_name.startswith('_'):
            is_callable = callable(func)
            status = "CALLABLE" if is_callable else "NOT_CALLABLE"
            print(f"  {func_name:40s} {status}")
            if is_callable:
                callable_count += 1
    
    # Get all classes and their methods
    classes = inspect.getmembers(api_client, inspect.isclass)
    
    print(f"\nClasses and their methods:")
    print("-" * 70)
    
    total_methods = 0
    for class_name, cls in classes:
        if not class_name.startswith('_') and cls.__module__ == 'api_client':
            print(f"\nClass: {class_name}")
            methods = inspect.getmembers(cls, inspect.isfunction)
            methods += inspect.getmembers(cls, inspect.ismethod)
            
            for method_name, method in methods:
                if not method_name.startswith('_'):
                    is_callable = callable(method)
                    status = "CALLABLE" if is_callable else "NOT_CALLABLE"
                    print(f"  - {method_name:38s} {status}")
                    callable_count += 1
                    total_methods += 1
    
    print(f"\n{'=' * 70}")
    print(f"STEP 4 RESULTS:")
    print(f"  Total module functions: {len(functions)}")
    print(f"  Total class methods: {total_methods}")
    print(f"  Total callable items: {callable_count}")
    print(f"  Status: PASS" if callable_count > 0 else "  Status: FAIL")
    print(f"{'=' * 70}\n")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
