"""
Pytest configuration and fixtures for AIPMS tests.

Provides fixtures to reset global state between tests to ensure
test isolation and prevent state leakage.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_models_cache():
    """Reset the models cache before each test to ensure test isolation."""
    try:
        from api.main import get_models
    except ImportError:
        yield
        return

    models = get_models()
    yield
    if hasattr(models, "clear"):
        models.clear()
