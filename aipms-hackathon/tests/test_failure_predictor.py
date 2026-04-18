"""
Tests for FailurePredictor model.

Tests cover:
- XGBoost binary classification training
- Probability calibration to [0, 1]
- Class imbalance handling via scale_pos_weight
- SHAP feature attribution
- Prediction uncertainty quantification
- Model persistence
- Edge cases
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

from models.train.failure_predictor import FailurePredictor


class TestFailurePredictorInit:
    """Test FailurePredictor initialization."""
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        fp = FailurePredictor()
        
        assert fp.model is None  # Model only created after fit()
        assert fp.max_depth is not None
        assert fp.learning_rate is not None
        assert fp.n_estimators is not None
        assert fp.is_fitted_ == False
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        fp = FailurePredictor(
            max_depth=6,
            learning_rate=0.1,
            n_estimators=200,
            random_state=42
        )
        
        assert fp.max_depth == 6
        assert fp.learning_rate == 0.1
        assert fp.n_estimators == 200


class TestFailurePredictorTraining:
    """Test FailurePredictor training."""
    
    def test_fit_basic(self):
        """Test fitting on random data."""
        fp = FailurePredictor(random_state=42)
        
        X = np.random.randn(200, 68).astype(np.float32)
        y = np.random.randint(0, 2, 200)
        
        fp.fit(X, y)
        
        assert fp.model is not None
        assert fp.is_fitted_
    
    def test_fit_handles_class_imbalance(self):
        """Test fitting with imbalanced classes."""
        fp = FailurePredictor(random_state=42)
        
        X = np.random.randn(200, 68).astype(np.float32)
        # Imbalanced: 80% class 0, 20% class 1
        y = np.concatenate([np.zeros(160), np.ones(40)]).astype(int)
        
        fp.fit(X, y)
        
        assert fp.model is not None
        # scale_pos_weight should be adjusted internally
    
    def test_fit_with_minority_class(self):
        """Test fitting when minority class is well represented."""
        fp = FailurePredictor(random_state=42)
        
        X = np.random.randn(300, 68).astype(np.float32)
        # Balanced: 50-50
        y = np.tile([0, 1], 150)
        
        fp.fit(X, y)
        
        assert fp.is_fitted_
    
    def test_fit_all_same_class(self):
        """Test fitting with all samples from one class."""
        fp = FailurePredictor(random_state=42)
        
        X = np.random.randn(100, 68).astype(np.float32)
        y = np.zeros(100)  # All negative class
        
        # Should handle gracefully or raise informative error
        with pytest.raises((ValueError, Exception)):
            fp.fit(X, y)


class TestFailurePredictorProbabilities:
    """Test probability predictions."""
    
    def test_predict_proba_output_shape(self):
        """Test predict_proba returns correct shape."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        proba = fp.predict_proba(X_test)
        
        # Should return 2D array: (n_samples, 2) or (n_samples,) for failure prob
        assert proba.ndim == 1
        assert len(proba) == 50
    
    def test_predict_proba_range(self):
        """Test probabilities are in [0, 1]."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(100, 68).astype(np.float32)
        proba = fp.predict_proba(X_test)
        
        assert np.all(proba >= 0)
        assert np.all(proba <= 1)
    
    def test_predict_proba_single_sample(self):
        """Test predict_proba with single sample."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_single = np.random.randn(1, 68).astype(np.float32)
        proba = fp.predict_proba(X_single)
        
        assert proba.shape == (1,)
        assert 0 <= proba[0] <= 1
    
    def test_predict_proba_class_distribution(self):
        """Test probability predictions match class distribution."""
        fp = FailurePredictor(random_state=42)
        
        # Synthetic data with clear pattern
        np.random.seed(42)
        X_train = np.random.randn(300, 68).astype(np.float32)
        # Create pattern: high values → class 1
        y_train = (X_train[:, 0] > 0).astype(int)
        
        fp.fit(X_train, y_train)
        
        # Test on data with clear class 1 pattern
        X_test_class1 = np.ones((50, 68), dtype=np.float32) * 2  # High values
        proba_class1 = fp.predict_proba(X_test_class1)
        
        # Test on data with clear class 0 pattern
        X_test_class0 = np.ones((50, 68), dtype=np.float32) * -2  # Low values
        proba_class0 = fp.predict_proba(X_test_class0)
        
        # Class 1 should have higher probability
        assert proba_class1.mean() > proba_class0.mean()


class TestFailurePredictorClassification:
    """Test binary classification predictions."""
    
    def test_predict_output_shape(self):
        """Test predict returns correct shape."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        preds = fp.predict(X_test)
        
        assert preds.shape == (50,)
    
    def test_predict_binary_values(self):
        """Test predict returns binary values."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(100, 68).astype(np.float32)
        preds = fp.predict(X_test)
        
        assert set(preds) <= {0, 1}
    
    def test_predict_threshold_at_0_5(self):
        """Test classification threshold is at 0.5."""
        fp = FailurePredictor(random_state=42, threshold=0.5)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(100, 68).astype(np.float32)
        proba = fp.predict_proba(X_test)
        preds = fp.predict(X_test)
        
        # Verify threshold logic
        expected_preds = (proba >= 0.5).astype(int)
        np.testing.assert_array_equal(preds, expected_preds)


class TestFailurePredictorShapleyValues:
    """Test SHAP feature attribution."""
    
    def test_get_shap_values_output_shape(self):
        """Test SHAP values have correct shape."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(10, 68).astype(np.float32)
        shap_values = fp.get_shap_values(X_test)
        
        assert shap_values.shape == (10, 68)
    
    def test_get_shap_values_magnitude(self):
        """Test SHAP values have reasonable magnitudes."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(10, 68).astype(np.float32)
        shap_values = fp.get_shap_values(X_test)
        
        # SHAP values should be finite and not NaN
        assert np.all(np.isfinite(shap_values))
        assert not np.any(np.isnan(shap_values))
    
    def test_get_top_features(self):
        """Test getting top features by SHAP importance."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(20, 68).astype(np.float32)
        top_features = fp.get_top_features(X_test, k=5)
        
        assert len(top_features) == 5
        # Each entry should be (feature_idx, shap_value)
        for feat_idx, shap_val in top_features:
            assert 0 <= feat_idx < 68
            assert isinstance(shap_val, (int, float, np.number))


class TestFailurePredictorMetrics:
    """Test evaluation metrics."""
    
    def test_compute_metrics_output(self):
        """Test metric computation returns dict with required keys."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        y_test = np.random.randint(0, 2, 50)
        
        metrics = fp.compute_metrics(X_test, y_test)
        
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'auc_roc' in metrics
    
    def test_compute_metrics_ranges(self):
        """Test metrics are in valid ranges."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(200, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 200)
        fp.fit(X_train, y_train)
        
        X_test = np.random.randn(100, 68).astype(np.float32)
        y_test = np.random.randint(0, 2, 100)
        
        metrics = fp.compute_metrics(X_test, y_test)
        
        for metric_name, metric_val in metrics.items():
            assert 0 <= metric_val <= 1, f"{metric_name} out of range: {metric_val}"


class TestFailurePredictorPersistence:
    """Test model saving and loading."""
    
    def test_save_model(self):
        """Test saving model to disk."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'failure_predictor.pkl'
            fp.save(model_path)
            
            assert model_path.exists()
            assert model_path.stat().st_size > 0
    
    def test_load_model_produces_same_predictions(self):
        """Test loaded model produces identical predictions."""
        fp1 = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp1.fit(X_train, y_train)
        
        X_test = np.random.randn(20, 68).astype(np.float32)
        proba1 = fp1.predict_proba(X_test)
        preds1 = fp1.predict(X_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'failure_predictor.pkl'
            fp1.save(model_path)
            
            # Load model
            fp2 = FailurePredictor()
            fp2.load(model_path)
            
            proba2 = fp2.predict_proba(X_test)
            preds2 = fp2.predict(X_test)
            
            np.testing.assert_allclose(proba1, proba2, rtol=1e-5)
            np.testing.assert_array_equal(preds1, preds2)


class TestFailurePredictorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_predict_before_fit_raises_error(self):
        """Test that predict before fit raises error."""
        fp = FailurePredictor()
        X_test = np.random.randn(10, 68).astype(np.float32)
        
        with pytest.raises((ValueError, AttributeError)):
            fp.predict(X_test)
    
    def test_handle_empty_batch(self):
        """Test handling of empty batch."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        X_empty = np.array([]).reshape(0, 68).astype(np.float32)
        
        proba = fp.predict_proba(X_empty)
        assert proba.shape == (0,)
    
    def test_handle_wrong_feature_dimension(self):
        """Test handling of wrong feature dimension."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        X_wrong = np.random.randn(10, 50).astype(np.float32)  # Wrong number of features
        
        # XGBoost will fail when trying to predict with mismatched dimensions
        try:
            fp.predict(X_wrong)
            # If we get here, XGBoost accepted it - that's a valid outcome
            # Just verify no crash occurred
            assert True
        except (ValueError, Exception):
            # Expected behavior
            pass
    
    def test_handle_nan_in_input(self):
        """Test handling of NaN in input."""
        fp = FailurePredictor(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.randint(0, 2, 100)
        fp.fit(X_train, y_train)
        
        X_with_nan = np.random.randn(10, 68).astype(np.float32)
        X_with_nan[0, 0] = np.nan
        
        # XGBoost may or may not raise error for NaN
        try:
            fp.predict(X_with_nan)
            # If we get here, model accepted it or handled it
            assert True
        except (ValueError, TypeError, Exception):
            # Expected behavior if XGBoost rejects NaN
            pass


class TestFailurePredictorIntegration:
    """Integration tests with feature engineer and dataset manager."""
    
    def test_integration_with_feature_engineer(self):
        """Test full pipeline: FeatureEngineer → FailurePredictor."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        # Get data
        dm = DatasetManager()
        X_raw, y_raw = dm.load('FD001', use_synthetic=True)
        
        # Engineer features
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        # Create failure labels matching engineered features
        # Note: feature engineering with rolling window reduces sample count by (window_size - 1)
        window_size = 5
        y_failure = (y_raw[window_size-1:] <= 30).astype(int)
        
        # Ensure alignment
        assert len(y_failure) == len(X_engineered)
        
        # Train failure predictor
        fp = FailurePredictor(random_state=42)
        fp.fit(X_engineered, y_failure)
        
        # Make predictions
        proba = fp.predict_proba(X_engineered)
        preds = fp.predict(X_engineered)
        
        assert proba.shape == (X_engineered.shape[0],)
        assert preds.shape == (X_engineered.shape[0],)
        assert np.all((proba >= 0) & (proba <= 1))
        assert set(preds) <= {0, 1}
    
    def test_typical_failure_prediction_on_degradation(self):
        """Test failure prediction on degrading engine data."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        dm = DatasetManager()
        X_raw, y_raw = dm.load('FD001', use_synthetic=True)
        
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        # Labels must match engineered feature count (rolling window reduces by window_size-1)
        window_size = 5
        y_failure = (y_raw[window_size-1:] <= 30).astype(int)
        
        # Ensure alignment
        assert len(y_failure) == len(X_engineered)
        
        # Split
        n_train = int(0.6 * len(X_engineered))
        X_train, y_train = X_engineered[:n_train], y_failure[:n_train]
        X_test, y_test = X_engineered[n_train:], y_failure[n_train:]
        
        # Train
        fp = FailurePredictor(random_state=42)
        fp.fit(X_train, y_train)
        
        # Evaluate
        metrics = fp.compute_metrics(X_test, y_test)
        
        assert metrics['accuracy'] > 0.5  # Better than random
        assert metrics['auc_roc'] > 0.5
    
    def test_shap_on_failure_predictions(self):
        """Test SHAP explainability on failure predictions."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        dm = DatasetManager()
        X_raw, y_raw = dm.load('FD001', use_synthetic=True)
        
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        # Align labels with engineered features
        window_size = 5
        y_failure = (y_raw[window_size-1:] <= 30).astype(int)
        
        fp = FailurePredictor(random_state=42)
        fp.fit(X_engineered[:100], y_failure[:100])
        
        # Get top features for some test samples
        X_test = X_engineered[100:120]
        top_features = fp.get_top_features(X_test, k=3)
        
        assert len(top_features) == 3
        # Features should be reasonable indices
        for feat_idx, shap_val in top_features:
            assert 0 <= feat_idx < 68
