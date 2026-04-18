"""
Tests for AnomalyDetector model.

Tests cover:
- Isolation Forest training and prediction
- Anomaly score calibration to [0, 1]
- Anomaly label classification (normal/warning/critical)
- Threshold-based anomaly detection
- Edge case handling
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import pickle

from models.train.anomaly_detector import AnomalyDetector


class TestAnomalyDetectorInit:
    """Test AnomalyDetector initialization."""
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        ad = AnomalyDetector()
        
        assert ad.model is not None
        assert ad.threshold_warning == 0.40
        assert ad.threshold_critical == 0.70
        assert ad.n_estimators == 100
        assert ad.contamination == 0.05
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        ad = AnomalyDetector(
            n_estimators=50,
            contamination=0.1,
            threshold_warning=0.35,
            threshold_critical=0.65,
            random_state=42
        )
        
        assert ad.n_estimators == 50
        assert ad.contamination == 0.1
        assert ad.threshold_warning == 0.35
        assert ad.threshold_critical == 0.65


class TestAnomalyDetectorTraining:
    """Test AnomalyDetector training."""
    
    def test_fit_basic(self):
        """Test fitting on random data."""
        ad = AnomalyDetector(random_state=42)
        X = np.random.randn(100, 68).astype(np.float32)
        
        ad.fit(X)
        
        assert ad.model is not None
        assert hasattr(ad.model, 'predict')
    
    def test_fit_with_constant_features(self):
        """Test fitting with some constant features."""
        ad = AnomalyDetector(random_state=42)
        X = np.random.randn(100, 68).astype(np.float32)
        X[:, 0] = 5.0  # Make first feature constant
        
        # Should not crash
        ad.fit(X)
        assert ad.model is not None
    
    def test_fit_updates_state(self):
        """Test that fitting updates model state."""
        ad = AnomalyDetector(random_state=42)
        assert ad.model is not None  # Created on init
        
        X = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X)
        
        # Model should have been trained
        scores = ad.model.score_samples(X)
        assert scores is not None


class TestAnomalyDetectorScores:
    """Test anomaly score computation."""
    
    def test_score_samples_output_shape(self):
        """Test score_samples returns correct shape."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_test = np.random.randn(20, 68).astype(np.float32)
        scores = ad.score_samples(X_test)
        
        assert scores.shape == (20,)
        assert scores.dtype in [np.float32, np.float64]
    
    def test_score_samples_range(self):
        """Test anomaly scores are in valid range."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        scores = ad.score_samples(X_test)
        
        # Scores should be between 0 and 1 (calibrated)
        assert np.all(scores >= 0)
        assert np.all(scores <= 1)
    
    def test_score_samples_distinguishes_outliers(self):
        """Test that outliers get higher scores than normal data."""
        ad = AnomalyDetector(random_state=42, contamination=0.05)
        
        # Training data
        X_train = np.random.randn(200, 68).astype(np.float32)
        ad.fit(X_train)
        
        # Normal test data (from same distribution)
        X_normal = np.random.randn(20, 68).astype(np.float32)
        
        # Outlier test data (extreme values)
        X_outliers = np.random.randn(20, 68).astype(np.float32) * 5  # 5x variance
        
        scores_normal = ad.score_samples(X_normal)
        scores_outliers = ad.score_samples(X_outliers)
        
        # Outliers should have higher mean score
        assert scores_outliers.mean() > scores_normal.mean()
    
    def test_score_samples_single_row(self):
        """Test score_samples with single sample."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_single = np.random.randn(1, 68).astype(np.float32)
        scores = ad.score_samples(X_single)
        
        assert scores.shape == (1,)
        assert 0 <= scores[0] <= 1


class TestAnomalyDetectorLabels:
    """Test anomaly label classification."""
    
    def test_predict_output_shape(self):
        """Test predict returns correct shape."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_test = np.random.randn(20, 68).astype(np.float32)
        labels = ad.predict(X_test)
        
        assert labels.shape == (20,)
    
    def test_predict_valid_labels(self):
        """Test predict returns valid label values."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_test = np.random.randn(50, 68).astype(np.float32)
        labels = ad.predict(X_test)
        
        # Should only contain valid label values
        valid_labels = {'normal', 'warning', 'critical'}
        assert set(labels) <= valid_labels
    
    def test_predict_normal_threshold(self):
        """Test normal classification threshold logic."""
        ad = AnomalyDetector(
            random_state=42,
            threshold_warning=0.40,
            threshold_critical=0.70,
            contamination=0.05
        )
        X_train = np.random.randn(500, 68).astype(np.float32)
        ad.fit(X_train)
        
        # Generate test data
        X_test = np.random.randn(100, 68).astype(np.float32)
        
        scores = ad.score_samples(X_test)
        labels = ad.predict(X_test)
        
        # Verify threshold logic: labels should match scores
        for score, label in zip(scores, labels):
            if score < 0.40:
                assert label == 'normal', f"Score {score:.3f} < 0.40, expected 'normal' but got '{label}'"
            elif score < 0.70:
                assert label == 'warning', f"Score {score:.3f} in [0.40, 0.70), expected 'warning' but got '{label}'"
            else:
                assert label == 'critical', f"Score {score:.3f} >= 0.70, expected 'critical' but got '{label}'"
    
    def test_predict_threshold_ordering(self):
        """Test threshold ordering: normal < warning < critical."""
        ad = AnomalyDetector(
            random_state=42,
            threshold_warning=0.40,
            threshold_critical=0.70
        )
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        # Create data with varying anomaly levels
        # Use different random states to get different distributions
        np.random.seed(0)
        X_test = np.random.randn(100, 68).astype(np.float32)
        
        scores = ad.score_samples(X_test)
        labels = ad.predict(X_test)
        
        # Verify threshold logic
        for i, (score, label) in enumerate(zip(scores, labels)):
            if score < 0.40:
                assert label == 'normal', f"Row {i}: score={score:.3f}, expected 'normal' but got '{label}'"
            elif score < 0.70:
                assert label == 'warning', f"Row {i}: score={score:.3f}, expected 'warning' but got '{label}'"
            else:
                assert label == 'critical', f"Row {i}: score={score:.3f}, expected 'critical' but got '{label}'"


class TestAnomalyDetectorPersistence:
    """Test saving and loading model."""
    
    def test_save_model(self):
        """Test saving model to disk."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'anomaly_detector.pkl'
            ad.save(model_path)
            
            assert model_path.exists()
            assert model_path.stat().st_size > 0
    
    def test_load_model_produces_same_predictions(self):
        """Test loaded model produces identical predictions."""
        ad1 = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad1.fit(X_train)
        
        X_test = np.random.randn(20, 68).astype(np.float32)
        scores1 = ad1.score_samples(X_test)
        labels1 = ad1.predict(X_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'anomaly_detector.pkl'
            ad1.save(model_path)
            
            # Load model
            ad2 = AnomalyDetector()
            ad2.load(model_path)
            
            scores2 = ad2.score_samples(X_test)
            labels2 = ad2.predict(X_test)
            
            np.testing.assert_allclose(scores1, scores2, rtol=1e-5)
            np.testing.assert_array_equal(labels1, labels2)


class TestAnomalyDetectorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_predict_before_fit_raises_error(self):
        """Test that predict before fit raises error."""
        ad = AnomalyDetector()
        X_test = np.random.randn(10, 68).astype(np.float32)
        
        # Should raise error if not fitted
        with pytest.raises((ValueError, AttributeError)):
            ad.predict(X_test)
    
    def test_handle_empty_batch(self):
        """Test handling of empty batch."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_empty = np.array([]).reshape(0, 68).astype(np.float32)
        
        # Should handle gracefully
        scores = ad.score_samples(X_empty)
        assert scores.shape == (0,)
    
    def test_handle_nan_in_input(self):
        """Test handling of NaN values in input."""
        ad = AnomalyDetector(random_state=42)
        X_train = np.random.randn(100, 68).astype(np.float32)
        ad.fit(X_train)
        
        X_with_nan = np.random.randn(10, 68).astype(np.float32)
        X_with_nan[0, 0] = np.nan
        
        # Model handles NaN gracefully (Isolation Forest is robust to NaN)
        scores = ad.score_samples(X_with_nan)
        assert scores.shape == (10,)
        assert not np.isnan(scores).all()  # Not all NaN values in output
    
    def test_identical_samples(self):
        """Test with all identical samples."""
        ad = AnomalyDetector(random_state=42)
        X_identical = np.ones((100, 68), dtype=np.float32)
        
        # Should not crash
        ad.fit(X_identical)
        
        scores = ad.score_samples(X_identical)
        assert scores is not None
        assert len(scores) == 100


class TestAnomalyDetectorIntegration:
    """Integration tests with FeatureEngineer."""
    
    def test_integration_with_feature_engineer(self):
        """Test full pipeline: FeatureEngineer → AnomalyDetector."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        # Get data
        dm = DatasetManager()
        X_raw, y = dm.load('FD001', use_synthetic=True)
        
        # Engineer features
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        # Train anomaly detector
        ad = AnomalyDetector(random_state=42)
        ad.fit(X_engineered)
        
        # Make predictions
        scores = ad.score_samples(X_engineered)
        labels = ad.predict(X_engineered)
        
        assert scores.shape == (X_engineered.shape[0],)
        assert labels.shape == (X_engineered.shape[0],)
        assert np.all((scores >= 0) & (scores <= 1))
        assert set(labels) <= {'normal', 'warning', 'critical'}
    
    def test_typical_anomaly_distribution(self):
        """Test typical anomaly detection on degradation data."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        dm = DatasetManager()
        X_raw, y = dm.load('FD001', use_synthetic=True)
        
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        ad = AnomalyDetector(contamination=0.05, random_state=42)
        ad.fit(X_engineered)
        
        labels = ad.predict(X_engineered)
        
        # Should have some variety in predictions
        # At least some normal, some warning or critical
        label_counts = {label: np.sum(labels == label) for label in {'normal', 'warning', 'critical'}}
        
        assert label_counts['normal'] > 0, "Should have some normal samples"
        # May have warning/critical but at least anomalies are detected
        has_anomalies = label_counts['warning'] > 0 or label_counts['critical'] > 0
        assert has_anomalies, "Should detect some anomalies"
    
    def test_sequential_predictions(self):
        """Test sequential predictions on engine degradation sequence."""
        from models.train.data_manager import DatasetManager
        from models.train.feature_engineer import FeatureEngineer
        
        dm = DatasetManager()
        X_raw, y = dm.load('FD001', use_synthetic=True)
        
        fe = FeatureEngineer()
        X_engineered = fe.process(X_raw)
        
        ad = AnomalyDetector(random_state=42)
        ad.fit(X_engineered[:100])  # Train on first 100 samples
        
        # Predict on remaining samples
        scores = ad.score_samples(X_engineered[100:])
        
        # Scores should be reasonable
        assert np.all(~np.isnan(scores))
        assert np.all(~np.isinf(scores))
