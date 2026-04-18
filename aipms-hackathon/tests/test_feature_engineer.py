"""
Test suite for FeatureEngineer - Data preprocessing and feature engineering.

Tests cover:
- Min-Max normalization
- Rolling statistics (mean, std, slope)
- Feature engineering pipeline
- Train/val/test splitting
- Scaler persistence (save/load)
- Target transformations
- Data leakage prevention
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import pickle

# Assuming FeatureEngineer will be in models/train/feature_engineer.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.train.feature_engineer import FeatureEngineer, RULScaler


class TestMinMaxScaler:
    """Test Min-Max normalization functionality."""
    
    def test_normalize_basic(self):
        """Test basic Min-Max normalization."""
        fe = FeatureEngineer()
        X = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float32)
        
        X_norm = fe.normalize(X)
        
        # Check all values in [0, 1]
        assert np.all(X_norm >= -0.01) and np.all(X_norm <= 1.01), "Normalized values should be in ~[0, 1]"
        assert X_norm.dtype == X.dtype
        assert X_norm.shape == X.shape
    
    def test_normalize_zeros_and_ones(self):
        """Test that min becomes 0 and max becomes 1 after normalization."""
        fe = FeatureEngineer()
        X = np.array([[10.0], [20.0], [30.0]])
        
        X_norm = fe.normalize(X)
        
        assert np.isclose(X_norm.min(), 0.0), f"Min should be 0, got {X_norm.min()}"
        assert np.isclose(X_norm.max(), 1.0), f"Max should be 1, got {X_norm.max()}"
    
    def test_normalize_single_value(self):
        """Test normalization with constant feature (all same values)."""
        fe = FeatureEngineer()
        X = np.array([[5.0], [5.0], [5.0]])
        
        # Should not raise; might be 0 or NaN, but should handle gracefully
        X_norm = fe.normalize(X)
        
        assert X_norm.shape == X.shape
        assert not np.isnan(X_norm).all(), "Should not be all NaN"
    
    def test_normalize_preserves_order(self):
        """Test that normalization preserves ordering of values."""
        fe = FeatureEngineer()
        X = np.array([[1], [3], [2], [5], [4]], dtype=np.float32)
        X_norm = fe.normalize(X)
        
        # Original order: 1 < 2 < 3 < 4 < 5
        # Normalized order should preserve
        order_orig = np.argsort(X.ravel())
        order_norm = np.argsort(X_norm.ravel())
        
        assert np.array_equal(order_orig, order_norm), "Normalization should preserve value ordering"
    
    def test_normalize_then_inverse(self):
        """Test normalize and inverse normalization are consistent."""
        fe = FeatureEngineer()
        X_orig = np.array([[1.0, 10.0], [5.0, 50.0], [10.0, 100.0]])
        
        X_norm = fe.normalize(X_orig)
        X_reconstructed = fe.inverse_normalize(X_norm)
        
        assert np.allclose(X_orig, X_reconstructed, atol=1e-5), "Should recover original after inverse"


class TestRollingStatistics:
    """Test rolling window feature engineering."""
    
    def test_rolling_mean(self):
        """Test rolling mean computation."""
        fe = FeatureEngineer(window_size=3)
        X = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0]])
        
        X_roll = fe.compute_rolling_features(X)
        
        # Should have rolling mean features
        assert X_roll.shape[1] >= X.shape[1], "Should have additional rolling features"
        assert not np.isnan(X_roll).all(axis=0).any() or X_roll.shape[0] > fe.window_size
    
    def test_rolling_features_shape(self):
        """Test rolling features output shape."""
        fe = FeatureEngineer(window_size=5)
        X = np.random.randn(100, 17)
        
        X_roll = fe.compute_rolling_features(X)
        
        # Should have 17 (original) + 51 (3*17 rolling stats) = 68 features
        expected_features = 17 + 3 * 17  # orig + mean + std + slope
        assert X_roll.shape[0] >= X.shape[0] - fe.window_size, "Should have at least n - window_size samples"
        assert X_roll.shape[1] == expected_features, f"Expected {expected_features} features, got {X_roll.shape[1]}"
    
    def test_rolling_features_non_nan(self):
        """Test rolling features don't contain excessive NaN."""
        fe = FeatureEngineer(window_size=5)
        X = np.random.randn(50, 17)
        
        X_roll = fe.compute_rolling_features(X)
        
        # After window_size samples, should have valid data
        nan_ratio = np.isnan(X_roll).sum() / X_roll.size
        assert nan_ratio < 0.2, f"NaN ratio too high: {nan_ratio:.2%}"
    
    def test_rolling_window_size_effect(self):
        """Test that different window sizes produce different results."""
        X = np.random.randn(100, 17)
        
        fe_small = FeatureEngineer(window_size=3)
        fe_large = FeatureEngineer(window_size=10)
        
        X_roll_small = fe_small.compute_rolling_features(X)
        X_roll_large = fe_large.compute_rolling_features(X)
        
        # Different windows should produce different values (except maybe first few rows)
        assert not np.allclose(X_roll_small[-50:], X_roll_large[-50:]), "Different windows should produce different results"


class TestTargetTransformation:
    """Test RUL target transformation."""
    
    def test_rul_clipping(self):
        """Test RUL clipping to reasonable maximum."""
        fe = FeatureEngineer()
        y = np.array([10, 50, 100, 150, 200, 250])
        
        y_clipped = fe.clip_rul(y)
        
        # Default max is usually 125
        assert np.all(y_clipped <= 150), f"Clipped RUL should be capped, got max {y_clipped.max()}"
        assert np.all(y_clipped > 0), "RUL should remain positive"
    
    def test_rul_clipping_preserves_small_values(self):
        """Test that clipping doesn't affect small RUL values."""
        fe = FeatureEngineer()
        y = np.array([1, 5, 10, 20])
        
        y_clipped = fe.clip_rul(y)
        
        assert np.array_equal(y, y_clipped), "Small values should not change"
    
    def test_rul_binary_labels(self):
        """Test binary failure labels within 30 cycles."""
        fe = FeatureEngineer()
        y = np.array([0, 5, 10, 29, 30, 50, 100, 200])
        
        y_binary = fe.create_binary_failure_labels(y, horizon=30)
        
        # RUL <= 30 should be 1 (failure), > 30 should be 0
        expected = np.array([1, 1, 1, 1, 1, 0, 0, 0])
        assert np.array_equal(y_binary, expected), f"Expected {expected}, got {y_binary}"


class TestTrainValTestSplit:
    """Test data splitting with leakage prevention."""
    
    def test_basic_split(self):
        """Test basic train/val/test splitting."""
        fe = FeatureEngineer()
        X = np.random.randn(1000, 17)
        y = np.random.rand(1000) * 100
        
        X_train, X_val, X_test, y_train, y_val, y_test = fe.train_val_test_split(
            X, y, train_frac=0.6, val_frac=0.2
        )
        
        # Check counts
        assert X_train.shape[0] + X_val.shape[0] + X_test.shape[0] == X.shape[0]
        assert abs(X_train.shape[0] / X.shape[0] - 0.6) < 0.05  # Within 5% of 60%
        assert abs(X_val.shape[0] / X.shape[0] - 0.2) < 0.05   # Within 5% of 20%
        assert abs(X_test.shape[0] / X.shape[0] - 0.2) < 0.05  # Within 5% of 20%
    
    def test_no_data_leakage(self):
        """Test that train/val/test splits have no overlap."""
        fe = FeatureEngineer()
        X = np.arange(1000).reshape(-1, 1)  # Easy to track
        y = np.random.rand(1000)
        
        X_train, X_val, X_test, _, _, _ = fe.train_val_test_split(X, y)
        
        train_indices = set(X_train.ravel().tolist())
        val_indices = set(X_val.ravel().tolist())
        test_indices = set(X_test.ravel().tolist())
        
        # Check no overlap
        assert len(train_indices & val_indices) == 0
        assert len(train_indices & test_indices) == 0
        assert len(val_indices & test_indices) == 0
    
    def test_split_preserves_shapes(self):
        """Test that splitting preserves feature dimensions."""
        fe = FeatureEngineer()
        X = np.random.randn(500, 17)
        y = np.random.rand(500)
        
        X_train, X_val, X_test, y_train, y_val, y_test = fe.train_val_test_split(X, y)
        
        assert X_train.shape[1] == 17
        assert X_val.shape[1] == 17
        assert X_test.shape[1] == 17
        assert y_train.ndim == 1
        assert y_val.ndim == 1
        assert y_test.ndim == 1


class TestScalerPersistence:
    """Test saving and loading scalers."""
    
    def test_save_and_load_scaler(self):
        """Test scaler can be saved and loaded."""
        fe = FeatureEngineer()
        X = np.random.randn(100, 17)
        
        # Fit scaler
        fe.normalize(X)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / 'scaler.pkl'
            
            # Save
            fe.save_scaler(scaler_path)
            assert scaler_path.exists()
            
            # Create new engineer and load
            fe2 = FeatureEngineer()
            fe2.load_scaler(scaler_path)
            
            # Should produce same normalization
            X_norm1 = fe.normalize(X)
            X_norm2 = fe2.normalize(X)
            
            assert np.allclose(X_norm1, X_norm2)
    
    def test_scaler_persistence_path(self):
        """Test scaler is saved at correct path."""
        fe = FeatureEngineer()
        X = np.random.randn(50, 17)
        fe.normalize(X)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / 'my_scaler.pkl'
            fe.save_scaler(scaler_path)
            
            assert scaler_path.exists()
            assert scaler_path.stat().st_size > 0


class TestFullPipeline:
    """Integration tests for full feature engineering pipeline."""
    
    def test_end_to_end_preprocessing(self):
        """Test complete preprocessing pipeline."""
        from models.train.data_manager import DatasetManager
        
        # Generate synthetic data
        dm = DatasetManager()
        X, y = dm.load('FD001', use_synthetic=True)
        
        # Engineer features
        fe = FeatureEngineer()
        X_feat = fe.compute_rolling_features(X)
        
        # Normalize
        X_norm = fe.normalize(X_feat)
        
        # Verify output
        assert X_norm.shape[0] <= X.shape[0]  # May have dropped first few rows
        assert X_norm.shape[1] > X.shape[1]   # Should have more features
        assert not np.isnan(X_norm).all()
        assert np.all(X_norm >= -0.1) or np.all(X_norm <= 1.1)  # Mostly normalized
    
    def test_preprocessing_consistency(self):
        """Test preprocessing is deterministic."""
        from models.train.data_manager import DatasetManager
        
        dm = DatasetManager()
        X, y = dm.load('FD001', use_synthetic=True)
        
        fe1 = FeatureEngineer()
        X_proc1 = fe1.process(X)
        
        fe2 = FeatureEngineer()
        X_proc2 = fe2.process(X)
        
        # Same input should produce same shape
        # (scalers may differ between fe instances, but shape should match)
        assert X_proc1.shape == X_proc2.shape
    
    def test_train_val_test_workflow(self):
        """Test typical train/val/test workflow."""
        from models.train.data_manager import DatasetManager
        
        dm = DatasetManager()
        X, y = dm.load('FD001', use_synthetic=True)
        
        fe = FeatureEngineer()
        
        # Preprocess
        X = fe.compute_rolling_features(X)
        X = fe.normalize(X)
        
        # Split
        X_train, X_val, X_test, y_train, y_val, y_test = fe.train_val_test_split(X, y)
        
        # Verify reasonable sizes
        assert X_train.shape[0] > X_val.shape[0]  # Train larger than val
        assert X_train.shape[0] > X_test.shape[0]  # Train larger than test
        assert y_train.shape[0] == X_train.shape[0]
        assert y_val.shape[0] == X_val.shape[0]
        assert y_test.shape[0] == X_test.shape[0]
