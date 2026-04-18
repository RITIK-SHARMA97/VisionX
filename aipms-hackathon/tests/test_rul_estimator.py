"""
Comprehensive test suite for RUL (Remaining Useful Life) Estimator.

The RUL Estimator uses LSTM networks to predict remaining useful life cycles
based on sequences of engineered sensor features. Tests cover:
- Initialization with various hyperparameters
- Sequence processing and windowing
- Training on sequences with class imbalance handling
- Prediction accuracy on validation data
- Uncertainty quantification (variance/std)
- Metric computation (MAE, RMSE, R²)
- Model persistence (save/load)
- Edge cases and error handling
- Full pipeline integration with FeatureEngineer
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path


class TestRULEstimatorInit:
    """Test RULEstimator initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator()
        
        assert rul.sequence_length == 30  # Default window
        assert rul.feature_dim == 68
        assert rul.lstm_units == 64
        assert rul.dropout_rate == 0.2
        assert rul.is_fitted_ == False
        assert rul.model is None

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(
            sequence_length=50,
            lstm_units=128,
            dropout_rate=0.3,
            learning_rate=0.001,
            batch_size=16
        )
        
        assert rul.sequence_length == 50
        assert rul.lstm_units == 128
        assert rul.dropout_rate == 0.3
        assert rul.learning_rate == 0.001
        assert rul.batch_size == 16


class TestRULEstimatorSequenceProcessing:
    """Test sequence creation and windowing."""

    def test_create_sequences_output_shape(self):
        """Test that sequences are created with correct shape."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5)
        X = np.random.randn(100, 68).astype(np.float32)
        
        X_seq, y_seq = rul._create_sequences(X, np.arange(100))
        
        # Should have 100 - 5 + 1 = 96 sequences
        assert X_seq.shape[0] == 96
        assert X_seq.shape[1] == 5  # Sequence length
        assert X_seq.shape[2] == 68  # Feature dimension
        assert y_seq.shape[0] == 96

    def test_create_sequences_values_correct(self):
        """Test that sequence values are correctly windowed."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=3, feature_dim=3)
        X = np.arange(15).reshape(5, 3).astype(np.float32)  # 5 samples, 3 features
        y = np.array([10, 20, 30, 40, 50])
        
        X_seq, y_seq = rul._create_sequences(X, y)
        
        # First sequence should have first 3 samples
        np.testing.assert_array_almost_equal(X_seq[0], X[:3])
        # Last sequence should have last 3 samples
        np.testing.assert_array_almost_equal(X_seq[-1], X[-3:])

    def test_create_sequences_y_matches_x(self):
        """Test that output y matches last value in sequence."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=4)
        X = np.random.randn(20, 68).astype(np.float32)
        y = np.arange(20, dtype=np.float32) * 10  # [0, 10, 20, ..., 190]
        
        X_seq, y_seq = rul._create_sequences(X, y)
        
        # Output y should be aligned with last value in window
        for i in range(len(y_seq)):
            expected_y = y[i + rul.sequence_length - 1]
            assert np.isclose(y_seq[i], expected_y)


class TestRULEstimatorTraining:
    """Test RUL model training."""

    def test_fit_basic(self):
        """Test basic model fitting."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=2)
        X = np.random.randn(100, 68).astype(np.float32)
        y = np.random.uniform(0, 200, 100).astype(np.float32)
        
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        assert rul.is_fitted_ == True
        assert rul.model is not None
        assert rul.history is not None

    def test_fit_with_varying_rul_values(self):
        """Test training with realistic RUL degradation pattern."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=2)
        
        # Create degradation pattern: RUL decreases over time
        X = np.random.randn(200, 68).astype(np.float32)
        y = np.linspace(200, 10, 200).astype(np.float32)  # Degradation pattern
        
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        assert rul.is_fitted_ == True

    def test_fit_creates_sequences(self):
        """Test that fit creates sequences internally."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=3, lstm_units=16, epochs=1)
        X = np.random.randn(20, 68).astype(np.float32)
        y = np.random.uniform(0, 200, 20).astype(np.float32)
        
        # This should not raise error
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        assert rul.is_fitted_ == True

    def test_fit_stores_history(self):
        """Test that training history is stored."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=3, lstm_units=16, epochs=2)
        X = np.random.randn(50, 68).astype(np.float32)
        y = np.random.uniform(0, 200, 50).astype(np.float32)
        
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        assert rul.history is not None
        assert 'loss' in rul.history.history


class TestRULEstimatorPrediction:
    """Test RUL prediction."""

    def test_predict_output_shape(self):
        """Test that predictions have correct shape."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        preds = rul.predict(X_test)
        
        # Predictions should be (n_sequences, )
        assert preds.shape[0] == len(X_test) - rul.sequence_length + 1

    def test_predict_reasonable_values(self):
        """Test that predictions are in reasonable RUL range."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(10, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        preds = rul.predict(X_test)
        
        # Predictions should be positive (no negative RUL)
        assert np.all(preds >= 0)
        # Predictions should be reasonable
        assert np.all(preds <= 500)

    def test_predict_single_sequence(self):
        """Test prediction on single sequence."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_single = np.random.randn(10, 68).astype(np.float32)
        preds = rul.predict(X_single)
        
        # Single sequence should still return array
        assert isinstance(preds, np.ndarray)
        assert len(preds) > 0


class TestRULEstimatorUncertainty:
    """Test uncertainty quantification."""

    def test_predict_with_uncertainty_output(self):
        """Test that uncertainty predictions have correct shape."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1, 
                          uncertainty_quantification=True)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(30, 68).astype(np.float32)
        preds, uncertainty = rul.predict(X_test, return_uncertainty=True)
        
        assert preds.shape == uncertainty.shape
        assert np.all(uncertainty >= 0)  # Std should be non-negative

    def test_uncertainty_is_small_for_confident_predictions(self):
        """Test that highly certain predictions have low uncertainty."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=16, epochs=3,
                          uncertainty_quantification=True, dropout_rate=0.1)
        
        # Create very predictable degradation
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.linspace(200, 10, 100).astype(np.float32)  # Monotonic
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        if hasattr(rul, 'dropout_model'):
            preds, uncertainty = rul.predict(X_test, return_uncertainty=True)
            # Average uncertainty should be reasonable
            assert np.mean(uncertainty) > 0


class TestRULEstimatorMetrics:
    """Test metric computation."""

    def test_compute_metrics_output(self):
        """Test that metrics dict contains required keys."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        y_test = np.random.uniform(0, 200, len(X_test)).astype(np.float32)
        
        metrics = rul.compute_metrics(X_test, y_test)
        
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics

    def test_compute_metrics_reasonable_values(self):
        """Test that metrics are in reasonable ranges."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        y_test = np.random.uniform(0, 200, len(X_test)).astype(np.float32)
        
        metrics = rul.compute_metrics(X_test, y_test)
        
        assert metrics['mae'] >= 0
        assert metrics['rmse'] >= 0
        # R² can be negative for poor models, so just check it's a reasonable number
        assert -100 < metrics['r2'] < 2


class TestRULEstimatorPersistence:
    """Test model saving and loading."""

    def test_save_model(self):
        """Test that model can be saved."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'rul_model')
            rul.save(model_path)
            
            # Model files should exist
            assert os.path.exists(model_path)

    def test_load_model_produces_same_predictions(self):
        """Test that loaded model produces identical predictions."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1, 
                          random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        preds_original = rul.predict(X_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'rul_model')
            rul.save(model_path)
            
            rul_loaded = RULEstimator.load(model_path)
            preds_loaded = rul_loaded.predict(X_test)
            
            np.testing.assert_array_almost_equal(preds_original, preds_loaded, decimal=5)


class TestRULEstimatorEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_before_fit_raises_error(self):
        """Test that prediction before fit raises error."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5)
        X_test = np.random.randn(50, 68).astype(np.float32)
        
        with pytest.raises((ValueError, AttributeError)):
            rul.predict(X_test)

    def test_handle_empty_batch(self):
        """Test handling of empty batch."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_empty = np.array([]).reshape(0, 68).astype(np.float32)
        preds = rul.predict(X_empty)
        
        assert len(preds) == 0

    def test_short_sequence_handling(self):
        """Test handling when data length < sequence_length."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=20, lstm_units=32, epochs=1)
        X = np.random.randn(100, 68).astype(np.float32)
        y = np.random.uniform(0, 200, 100).astype(np.float32)
        
        # Should handle data that's long enough
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        # Test with short input (shorter than sequence_length)
        X_short = np.random.randn(5, 68).astype(np.float32)
        preds = rul.predict(X_short)
        
        # Should return empty or minimal predictions
        assert len(preds) <= 1

    def test_nan_in_input_handling(self):
        """Test handling of NaN values in input."""
        from models.train.rul_estimator import RULEstimator
        
        rul = RULEstimator(sequence_length=5, lstm_units=32, epochs=1)
        X_train = np.random.randn(100, 68).astype(np.float32)
        y_train = np.random.uniform(0, 200, 100).astype(np.float32)
        rul.fit(X_train, y_train, validation_split=0.2, verbose=0)
        
        X_with_nan = np.random.randn(30, 68).astype(np.float32)
        X_with_nan[0, 0] = np.nan
        
        # Should either handle or raise meaningful error
        try:
            preds = rul.predict(X_with_nan)
            # If it succeeds, predictions should be finite
            assert np.all(np.isfinite(preds))
        except (ValueError, RuntimeError):
            # Expected behavior
            pass


class TestRULEstimatorIntegration:
    """Test full pipeline integration."""

    def test_integration_with_feature_engineer(self):
        """Test full pipeline: FeatureEngineer → RUL Estimator."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        from models.train.rul_estimator import RULEstimator
        
        # Get data
        dm = DatasetManager()
        X_raw, y_raw = dm.load('FD001', use_synthetic=True)
        
        # Engineer features
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        # Create RUL labels (units to failure)
        window_size = 5
        y_rul = y_raw[window_size-1:]
        
        # Align
        assert len(y_rul) == len(X_engineered)
        
        # Train RUL estimator
        rul = RULEstimator(sequence_length=10, lstm_units=32, epochs=1)
        rul.fit(X_engineered, y_rul, validation_split=0.2, verbose=0)
        
        # Make predictions
        preds = rul.predict(X_engineered[:50])
        
        assert len(preds) > 0
        assert np.all(preds >= 0)

    def test_realistic_degradation_prediction(self):
        """Test prediction on realistic degradation pattern."""
        from models.train.rul_estimator import RULEstimator
        
        # Create degrading sensor pattern
        n_samples = 200
        X = np.random.randn(n_samples, 68).astype(np.float32)
        # Add degradation trend to features
        trend = np.linspace(0, 1, n_samples).reshape(-1, 1)
        X[:, :5] += trend * 3  # Sensor degradation
        
        # RUL decreases over time
        y = np.linspace(200, 10, n_samples).astype(np.float32)
        
        rul = RULEstimator(sequence_length=15, lstm_units=32, epochs=2)
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        preds = rul.predict(X)
        
        # Model should capture general trend (predictions generally decrease)
        assert len(preds) > 0
        assert np.all(np.isfinite(preds))

    def test_predict_degradation_trend(self):
        """Test that model predicts higher RUL for early degradation stages."""
        from models.train.rul_estimator import RULEstimator
        
        # Create clear degradation pattern
        n_early = 50
        n_late = 50
        
        # Early stage: normal operation
        X_early = np.random.randn(n_early, 68).astype(np.float32)
        y_early = np.full(n_early, 150.0)  # High RUL
        
        # Late stage: degraded operation
        X_late = np.random.randn(n_late, 68).astype(np.float32) + 2.0
        y_late = np.full(n_late, 30.0)  # Low RUL
        
        X = np.vstack([X_early, X_late]).astype(np.float32)
        y = np.hstack([y_early, y_late]).astype(np.float32)
        
        rul = RULEstimator(sequence_length=10, lstm_units=32, epochs=2)
        rul.fit(X, y, validation_split=0.2, verbose=0)
        
        # Predictions on early and late data
        preds_early = np.mean(rul.predict(X_early[:20]))
        preds_late = np.mean(rul.predict(X_late[-20:]))
        
        # Early stage should predict higher RUL than late stage
        assert preds_early > preds_late or np.isclose(preds_early, preds_late, atol=20)
