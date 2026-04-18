"""
Pytest configuration and fixtures for AIPMS tests.

Provides fixtures to reset global state between tests to ensure
test isolation and prevent state leakage.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_models_cache():
    """Reset the models cache before each test to ensure test isolation."""
    # Import here to avoid circular imports
    from api.main import models_cache
    
    # Reset all models cache entries before the test
    yield  # Run the test
    
    # Reset after the test as well (optional but good practice)
    models_cache["dataset_manager"] = None
    models_cache["feature_engineer"] = None
    models_cache["anomaly_detector"] = None
    models_cache["failure_predictor"] = None
    models_cache["rul_estimator"] = None
    models_cache["X_engineered"] = None
    models_cache["y_raw"] = None
    models_cache["X_raw"] = None
