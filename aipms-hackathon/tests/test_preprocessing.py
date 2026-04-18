"""
Comprehensive tests for ML data preprocessing pipeline (Phase 2B).
Tests cover: data loading, RUL labeling, normalization, feature engineering.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Import the preprocessing pipeline
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.train.preprocess import PreprocessingPipeline


class TestPreprocessingPipeline:
    """Test suite for PreprocessingPipeline class."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_cmapss_data(self, temp_data_dir):
        """
        Create sample C-MAPSS-like data for testing.
        Format: engine_id, cycle, op_setting_1, op_setting_2, op_setting_3, 
                sensor_2, ..., sensor_21
        """
        # Create FD001 training file
        raw_dir = Path(temp_data_dir) / 'raw'
        raw_dir.mkdir(exist_ok=True, parents=True)
        
        # 3 engines, 10-15 cycles each
        # Note: Create cycles 1..n_cycles, but max cycle in lifecycle is n_cycles + 5
        data = []
        max_cycles_list = []
        for engine_id in range(1, 4):
            n_cycles = 10 + engine_id * 2
            max_cycle_for_engine = n_cycles + 5  # Add 5 extra cycles to give positive RUL
            max_cycles_list.append(max_cycle_for_engine)
            
            for cycle in range(1, n_cycles + 1):
                # op_setting_1, op_setting_2, op_setting_3
                row = [engine_id, cycle, 34.0, 0.84, 100.0]
                # 14 active sensors
                for sensor_idx in range(14):
                    row.append(50.0 + np.random.randn() * 5.0)
                data.append(row)
        
        df = pd.DataFrame(data)
        train_file = raw_dir / 'train_FD001.txt'
        df.to_csv(train_file, sep=' ', header=False, index=False)
        
        # Create RUL file (max cycles per engine)
        rul_file = raw_dir / 'RUL_FD001.txt'
        with open(rul_file, 'w') as f:
            for rul in max_cycles_list:
                f.write(f"{rul}\n")
        
        return raw_dir
    
    def test_preprocessing_pipeline_init(self, temp_data_dir):
        """Test PreprocessingPipeline initialization."""
        pipeline = PreprocessingPipeline(data_dir=temp_data_dir)
        assert pipeline.data_dir == Path(temp_data_dir)
    
    def test_load_cmapss_data_structure(self, sample_cmapss_data):
        """Test loading C-MAPSS data returns correct structure."""
        # sample_cmapss_data is the raw_dir, parent is the temp data dir
        data_dir = sample_cmapss_data.parent
        pipeline = PreprocessingPipeline(data_dir=str(data_dir / 'raw'))
        X, y, engine_ids = pipeline.load_cmapss_data(subset='FD001')
        
        # Check return types
        assert isinstance(X, np.ndarray), "X should be numpy array"
        assert isinstance(y, np.ndarray), "y should be numpy array"
        assert isinstance(engine_ids, np.ndarray), "engine_ids should be numpy array"
        
        # Check shapes match
        assert X.shape[0] == y.shape[0], "X and y should have same first dimension"
        assert X.shape[0] == engine_ids.shape[0], "X and engine_ids should match"
    
    def test_load_cmapss_data_values(self, sample_cmapss_data):
        """Test loaded data has correct values and no NaN."""
        # sample_cmapss_data is the raw_dir, parent is the temp data dir
        data_dir = sample_cmapss_data.parent
        pipeline = PreprocessingPipeline(data_dir=str(data_dir / 'raw'))
        X, y, engine_ids = pipeline.load_cmapss_data(subset='FD001')
        
        # Check for NaN values
        assert not np.isnan(X).any(), "X should not contain NaN values"
        assert not np.isnan(y).any(), "y should not contain NaN values"
        
        # Check feature count (19 features: 3 op_settings + 14 sensors, minus 2 index columns = 17)
        assert X.shape[1] == 17, f"Expected 17 features, got {X.shape[1]}"
        
        # Check y values are non-negative (RUL can be 0 at end of life)
        assert np.all(y >= 0), f"RUL values should be non-negative, got min: {y.min()}"
    
    def test_create_rul_labels_basic(self):
        """Test RUL label creation with simple data."""
        # Create simple test data: 2 engines, 5 cycles each
        data = {
            'engine_id': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            'cycle': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        pipeline = PreprocessingPipeline()
        rul = pipeline.create_rul_labels(df, max_rul=125)
        
        # Check RUL values: max_cycle - current_cycle
        # Engine 1: max=5, so RULs should be [4, 3, 2, 1, 0]
        # Engine 2: max=5, so RULs should be [4, 3, 2, 1, 0]
        expected = [4, 3, 2, 1, 0, 4, 3, 2, 1, 0]
        np.testing.assert_array_equal(rul, expected)
    
    def test_create_rul_labels_clipping(self):
        """Test RUL clipping at max_rul threshold."""
        data = {
            'engine_id': [1, 1, 1, 1, 1],
            'cycle': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        pipeline = PreprocessingPipeline()
        rul = pipeline.create_rul_labels(df, max_rul=3)
        
        # RUL values capped at 3: max(rul, 3) is not used, min(rul, 3)
        # So: [4→3, 3, 2, 1, 0]
        expected = [3, 3, 2, 1, 0]
        np.testing.assert_array_equal(rul, expected)
    
    def test_normalize_features_minmax(self):
        """Test MinMax normalization."""
        X = np.array([
            [0, 100],
            [50, 200],
            [100, 300]
        ], dtype=np.float32)
        
        pipeline = PreprocessingPipeline()
        X_normalized, scaler = pipeline.normalize_features(X, method='minmax')
        
        # Check shape preserved
        assert X_normalized.shape == X.shape
        
        # Check values are in [0, 1]
        assert np.all(X_normalized >= 0) and np.all(X_normalized <= 1), \
            "MinMax normalized values should be in [0, 1]"
        
        # Check first value (min) normalizes to 0
        assert X_normalized[0, 0] < 1e-6, "Min value should normalize to ~0"
        
        # Check last value (max) normalizes to 1
        assert X_normalized[2, 1] > 1 - 1e-6, "Max value should normalize to ~1"
        
        # Check scaler is MinMaxScaler
        assert isinstance(scaler, MinMaxScaler)
    
    def test_normalize_features_standard(self):
        """Test Standard (Z-score) normalization."""
        X = np.array([
            [0, 100],
            [50, 200],
            [100, 300]
        ], dtype=np.float32)
        
        pipeline = PreprocessingPipeline()
        X_normalized, scaler = pipeline.normalize_features(X, method='standard')
        
        # Check shape preserved
        assert X_normalized.shape == X.shape
        
        # Check mean ≈ 0 and std ≈ 1
        assert np.abs(X_normalized.mean(axis=0)).max() < 1e-6, "Normalized mean should be ~0"
        # Note: std might be slightly different due to sample vs population, so check it's close to 1
        assert np.abs(X_normalized.std(axis=0) - 1.0).max() < 0.5, "Normalized std should be ~1"
        
        # Check scaler is StandardScaler
        assert isinstance(scaler, StandardScaler)
    
    def test_normalize_features_inverse_transform(self):
        """Test that normalization can be inverted."""
        X_original = np.array([
            [0, 100],
            [50, 200],
            [100, 300]
        ], dtype=np.float32)
        
        pipeline = PreprocessingPipeline()
        X_normalized, scaler = pipeline.normalize_features(X_original, method='minmax')
        X_recovered = scaler.inverse_transform(X_normalized)
        
        # Check recovered values match original (within floating-point tolerance)
        np.testing.assert_array_almost_equal(X_recovered, X_original, decimal=5)
    
    def test_engineer_features_output_shape(self):
        """Test feature engineering produces correct shape."""
        X = np.random.randn(100, 14)  # 100 samples, 14 features
        window_size = 5
        
        pipeline = PreprocessingPipeline()
        X_engineered = pipeline.engineer_features(X, window_size=window_size)
        
        # Output should have original + rolling stats (mean, std, slope) per feature
        # Total: 14 + 14 (mean) + 14 (std) + 14 (slope) = 56 features
        expected_features = 14 * 4
        assert X_engineered.shape[1] == expected_features, \
            f"Expected {expected_features} features, got {X_engineered.shape[1]}"
        
        # Same number of samples
        assert X_engineered.shape[0] == X.shape[0]
    
    def test_engineer_features_no_nan(self):
        """Test feature engineering doesn't produce NaN values."""
        X = np.random.randn(50, 14)
        
        pipeline = PreprocessingPipeline()
        X_engineered = pipeline.engineer_features(X, window_size=5)
        
        # Check for NaN (may be present at start due to window, but should be minimal)
        nan_count = np.isnan(X_engineered).sum()
        assert nan_count == 0, f"Feature engineering produced {nan_count} NaN values"
    
    def test_engineer_features_rolling_mean(self):
        """Test that rolling mean features are computed correctly."""
        # Simple test: constant data should produce constant rolling mean
        X = np.ones((10, 1)) * 5.0  # 10 samples, 1 feature, all value 5
        
        pipeline = PreprocessingPipeline()
        X_engineered = pipeline.engineer_features(X, window_size=3)
        
        # Rolling mean of constant should be constant
        rolling_mean = X_engineered[:, 1]  # Second column is rolling mean
        assert np.allclose(rolling_mean[2:], 5.0, atol=1e-6), \
            "Rolling mean of constant data should be constant"
    
    def test_end_to_end_pipeline(self, sample_cmapss_data):
        """Test complete preprocessing pipeline end-to-end."""
        # sample_cmapss_data is the raw_dir, parent is the temp data dir
        data_dir = sample_cmapss_data.parent
        pipeline = PreprocessingPipeline(data_dir=str(data_dir / 'raw'))
        
        # Load data
        X, y, engine_ids = pipeline.load_cmapss_data(subset='FD001')
        
        # Normalize
        X_normalized, scaler = pipeline.normalize_features(X, method='minmax')
        
        # Engineer features
        X_engineered = pipeline.engineer_features(X_normalized, window_size=5)
        
        # Verify final output
        assert X_engineered.shape[0] > 0, "Pipeline should produce samples"
        # 17 features (3 op_settings + 14 sensors) × 4 (original + rolling_mean + rolling_std + rolling_slope) = 68
        assert X_engineered.shape[1] == 68, f"Pipeline should produce 68 engineered features, got {X_engineered.shape[1]}"
        assert not np.isnan(X_engineered).any(), "Pipeline should not produce NaN"
        assert not np.isnan(y).any(), "Pipeline should not produce NaN RUL"
    
    def test_scaler_persistence(self):
        """Test that scalers can be saved and loaded for consistency."""
        X_train = np.array([
            [0, 100],
            [50, 200],
            [100, 300]
        ], dtype=np.float32)
        
        X_test = np.array([
            [25, 150],
            [75, 250]
        ], dtype=np.float32)
        
        pipeline = PreprocessingPipeline()
        X_train_norm, scaler = pipeline.normalize_features(X_train, method='minmax')
        
        # Transform test data with same scaler
        X_test_norm = scaler.transform(X_test)
        
        # Verify test data is normalized using training statistics
        assert X_test_norm.shape == X_test.shape
        assert np.all(X_test_norm >= 0) and np.all(X_test_norm <= 1)


class TestDataQuality:
    """Test suite for data quality checks."""
    
    def test_detect_missing_values(self):
        """Test detection of missing values in data."""
        X = np.array([
            [1, 2, 3],
            [4, np.nan, 6],
            [7, 8, 9]
        ])
        
        missing_count = np.isnan(X).sum()
        assert missing_count == 1, "Should detect 1 missing value"
    
    def test_detect_outliers_zscore(self):
        """Test detection of outliers using z-score method."""
        X = np.array([1, 2, 3, 4, 5, 100])  # 100 is outlier
        
        z_scores = np.abs((X - X.mean()) / X.std())
        outliers = z_scores > 2.0  # Threshold for outlier detection
        
        assert outliers[-1] == True, f"Should identify 100 as outlier. Z-scores: {z_scores}"
        assert outliers[:-1].sum() == 0, "Should not identify others as outliers"


class TestFeatureEngineering:
    """Test suite for advanced feature engineering."""
    
    def test_rolling_std_computation(self):
        """Test rolling standard deviation computation."""
        X = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float32)
        
        # Compute rolling std with window=3
        from scipy import stats
        rolling_std = pd.Series(X).rolling(window=3).std().values
        
        # First 2 values should be NaN (not enough data)
        assert np.isnan(rolling_std[0]) and np.isnan(rolling_std[1])
        
        # Third value should be std([1,2,3]) with ddof=1 (pandas default)
        expected = np.std([1, 2, 3], ddof=1)  # Use ddof=1 for sample std
        assert np.isclose(rolling_std[2], expected), f"Rolling std should match manual calculation. Got {rolling_std[2]}, expected {expected}n. Got {rolling_std[2]}, expected {expected}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
