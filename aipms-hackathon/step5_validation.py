import sys

try:
    import config_constants as config
    
    print("=" * 70)
    print("STEP 5: CONFIGURATION LOAD - config_constants.py")
    print("=" * 70)
    
    # Get all UPPERCASE constants (configuration parameters)
    config_params = [attr for attr in dir(config) if attr.isupper() and not attr.startswith('_')]
    
    print(f"\nTotal configuration parameters found: {len(config_params)}\n")
    
    # Sort and display
    config_params.sort()
    print("Configuration Parameters:")
    print("-" * 70)
    
    for i, param in enumerate(config_params, 1):
        try:
            value = getattr(config, param)
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 40:
                value_str = value_str[:37] + "..."
            print(f"  {i:2d}. {param:40s} = {value_str}")
        except Exception as e:
            print(f"  {i:2d}. {param:40s} ERROR: {e}")
    
    # Check critical parameters
    print(f"\n{'=' * 70}")
    print("Critical Parameters Verification:")
    print("-" * 70)
    
    critical_params = [
        'MQTT_BROKER_HOST',
        'FAILURE_PREDICTION_HORIZON_DAYS',
        'API_PORT',
        'DASHBOARD_PORT'
    ]
    
    found_critical = 0
    for crit_param in critical_params:
        if crit_param in config_params:
            try:
                value = getattr(config, crit_param)
                print(f"  ✓ {crit_param:40s} = {value}")
                found_critical += 1
            except Exception as e:
                print(f"  ✗ {crit_param:40s} ERROR: {e}")
        else:
            print(f"  ✗ {crit_param:40s} NOT FOUND")
    
    print(f"\n{'=' * 70}")
    print(f"STEP 5 RESULTS:")
    print(f"  Total parameters loaded: {len(config_params)}")
    print(f"  Critical parameters found: {found_critical}/{len(critical_params)}")
    print(f"  Status: {'PASS' if len(config_params) >= 60 else 'FAIL'}")
    print(f"{'=' * 70}\n")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
