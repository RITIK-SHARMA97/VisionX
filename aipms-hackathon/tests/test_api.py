"""
Comprehensive test suite for AIPMS FastAPI endpoints.

Tests cover:
- Health check endpoint
- Data loading and feature engineering endpoints
- Model prediction endpoints (anomaly detection, failure prediction, RUL)
- Error handling and validation
- Response formats and status codes
- Integration with all trained models
"""

import pytest
import numpy as np
import json
from fastapi.testclient import TestClient


class TestAPIHealthCheck:
    """Test API health and status endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns 200."""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_endpoint(self):
        """Test /health endpoint."""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAPIDataEndpoints:
    """Test data loading and processing endpoints."""

    def test_load_dataset_valid(self):
        """Test loading valid dataset."""
        from api.main import app
        client = TestClient(app)
        
        response = client.post(
            "/data/load",
            json={"dataset": "FD001", "use_synthetic": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "n_samples" in data
        assert data["n_samples"] > 0

    def test_load_dataset_invalid(self):
        """Test loading invalid dataset raises error."""
        from api.main import app
        client = TestClient(app)
        
        response = client.post(
            "/data/load",
            json={"dataset": "INVALID", "use_synthetic": False}
        )
        
        assert response.status_code != 200

    def test_engineer_features(self):
        """Test feature engineering endpoint."""
        from api.main import app
        client = TestClient(app)
        
        # First load data
        response_load = client.post(
            "/data/load",
            json={"dataset": "FD001", "use_synthetic": True}
        )
        
        # Then engineer features
        response = client.post("/features/engineer", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "n_features" in data
        assert data["n_features"] == 68  # Standard feature count


class TestAnomalyDetectorAPI:
    """Test anomaly detection endpoints."""

    def test_anomaly_detector_train(self):
        """Test anomaly detector training endpoint."""
        from api.main import app
        client = TestClient(app)
        
        # Prepare data
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        
        # Train anomaly detector
        response = client.post(
            "/anomaly/train",
            json={"contamination": 0.1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "trained"

    def test_anomaly_detector_predict(self):
        """Test anomaly detection prediction."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/anomaly/train", json={"contamination": 0.1})
        
        # Predict on sample
        X_test = np.random.randn(10, 68).astype(np.float32)
        response = client.post(
            "/anomaly/predict",
            json={"X": X_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 10

    def test_anomaly_detector_predict_before_train(self):
        """Test prediction before training raises error."""
        from api.main import app
        client = TestClient(app)
        
        X_test = np.random.randn(10, 68).astype(np.float32)
        response = client.post(
            "/anomaly/predict",
            json={"X": X_test.tolist()}
        )
        
        # Should return error status
        assert response.status_code != 200


class TestFailurePredictorAPI:
    """Test failure prediction endpoints."""

    def test_failure_predictor_train(self):
        """Test failure predictor training endpoint."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        
        # Train failure predictor
        response = client.post(
            "/failure/train",
            json={"max_depth": 5, "learning_rate": 0.05}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_failure_predictor_predict_proba(self):
        """Test failure probability prediction."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/failure/train", json={})
        
        # Predict probabilities
        X_test = np.random.randn(5, 68).astype(np.float32)
        response = client.post(
            "/failure/predict_proba",
            json={"X": X_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "probabilities" in data
        assert len(data["probabilities"]) == 5

    def test_failure_predictor_predict(self):
        """Test binary failure prediction."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/failure/train", json={})
        
        # Binary predictions
        X_test = np.random.randn(5, 68).astype(np.float32)
        response = client.post(
            "/failure/predict",
            json={"X": X_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert set(data["predictions"]) <= {0, 1}

    def test_failure_predictor_shap_values(self):
        """Test SHAP feature importance."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/failure/train", json={})
        
        # Get SHAP values
        X_test = np.random.randn(2, 68).astype(np.float32)
        response = client.post(
            "/failure/shap_values",
            json={"X": X_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shap_values" in data
        assert len(data["shap_values"]) == 2


class TestRULEstimatorAPI:
    """Test RUL estimation endpoints."""

    def test_rul_estimator_train(self):
        """Test RUL estimator training endpoint."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        
        # Train RUL estimator
        response = client.post(
            "/rul/train",
            json={"sequence_length": 10, "lstm_units": 32, "epochs": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_rul_estimator_predict(self):
        """Test RUL prediction."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/rul/train", json={"epochs": 1})
        
        # Predict RUL
        X_test = np.random.randn(20, 68).astype(np.float32)
        response = client.post(
            "/rul/predict",
            json={"X": X_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0

    def test_rul_estimator_metrics(self):
        """Test RUL metrics computation."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/rul/train", json={"epochs": 1})
        
        # Compute metrics
        X_test = np.random.randn(50, 68).astype(np.float32)
        y_test = np.random.uniform(10, 200, 50)
        response = client.post(
            "/rul/metrics",
            json={"X": X_test.tolist(), "y": y_test.tolist()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mae" in data
        assert "rmse" in data
        assert "r2" in data


class TestAPIPipeline:
    """Test full pipeline integration."""

    def test_end_to_end_pipeline(self):
        """Test complete pipeline from data to predictions."""
        from api.main import app
        client = TestClient(app)
        
        # Load data
        r1 = client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        assert r1.status_code == 200
        
        # Engineer features
        r2 = client.post("/features/engineer", json={})
        assert r2.status_code == 200
        
        # Train anomaly detector
        r3 = client.post("/anomaly/train", json={"contamination": 0.1})
        assert r3.status_code == 200
        
        # Train failure predictor
        r4 = client.post("/failure/train", json={})
        assert r4.status_code == 200
        
        # Train RUL estimator
        r5 = client.post("/rul/train", json={"epochs": 1})
        assert r5.status_code == 200
        
        # Make predictions
        X_test = np.random.randn(10, 68).astype(np.float32)
        
        r6 = client.post("/anomaly/predict", json={"X": X_test.tolist()})
        assert r6.status_code == 200
        
        r7 = client.post("/failure/predict_proba", json={"X": X_test.tolist()})
        assert r7.status_code == 200
        
        r8 = client.post("/rul/predict", json={"X": X_test.tolist()})
        assert r8.status_code == 200

    def test_pipeline_persistence(self):
        """Test saving and loading models via API."""
        from api.main import app
        client = TestClient(app)
        
        # Setup and train
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/anomaly/train", json={})
        
        # Save models
        response = client.post("/models/save", json={"path": "/tmp/aipms_models"})
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAPIErrorHandling:
    """Test API error handling and validation."""

    def test_invalid_input_shape(self):
        """Test handling of invalid input shape."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/anomaly/train", json={})
        
        # Try to predict with wrong shape
        X_wrong = np.random.randn(10, 50).astype(np.float32)  # Wrong features
        response = client.post(
            "/anomaly/predict",
            json={"X": X_wrong.tolist()}
        )
        
        # Should fail validation
        assert response.status_code != 200

    def test_missing_required_parameter(self):
        """Test handling of missing required parameters."""
        from api.main import app
        client = TestClient(app)
        
        # Missing 'X' parameter
        response = client.post("/anomaly/predict", json={})
        
        assert response.status_code != 200

    def test_invalid_dataset_name(self):
        """Test handling of invalid dataset name."""
        from api.main import app
        client = TestClient(app)
        
        response = client.post(
            "/data/load",
            json={"dataset": "NONEXISTENT", "use_synthetic": False}
        )
        
        assert response.status_code != 200

    def test_model_not_trained(self):
        """Test prediction on untrained model."""
        from api.main import app
        client = TestClient(app)
        
        X_test = np.random.randn(10, 68).astype(np.float32)
        response = client.post(
            "/failure/predict",
            json={"X": X_test.tolist()}
        )
        
        # Should fail - model not trained
        assert response.status_code != 200


class TestAPIResponseFormats:
    """Test response format consistency."""

    def test_prediction_response_format(self):
        """Test that predictions follow standard format."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/failure/train", json={})
        
        # Get prediction
        X_test = np.random.randn(5, 68).astype(np.float32)
        response = client.post(
            "/failure/predict",
            json={"X": X_test.tolist()}
        )
        
        data = response.json()
        
        # Standard response should have predictions array
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 5

    def test_metrics_response_format(self):
        """Test that metrics follow standard format."""
        from api.main import app
        client = TestClient(app)
        
        # Setup
        client.post("/data/load", json={"dataset": "FD001", "use_synthetic": True})
        client.post("/features/engineer", json={})
        client.post("/failure/train", json={})
        
        # Get metrics
        X_test = np.random.randn(50, 68).astype(np.float32)
        y_test = np.random.uniform(0, 1, 50)
        response = client.post(
            "/failure/metrics",
            json={"X": X_test.tolist(), "y": y_test.tolist()}
        )
        
        data = response.json()
        
        # Standard metrics format
        assert isinstance(data, dict)
        assert all(isinstance(v, (int, float)) for v in data.values())
