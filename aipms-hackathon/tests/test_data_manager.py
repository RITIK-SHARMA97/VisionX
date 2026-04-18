"""
Test suite for DatasetManager - Dataset loading and validation.

Tests cover:
- Synthetic dataset generation
- Real dataset loading
- Data validation
- Caching mechanism
- Dataset registry
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Assuming DatasetManager will be in models/train/data_manager.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.train.data_manager import DatasetManager, DatasetRegistry


class TestDatasetRegistry:
    """Test dataset registry and metadata."""
    
    def test_registry_initialization(self):
        """Test registry initializes with known subsets."""
        registry = DatasetRegistry()
        assert 'FD001' in registry.subsets
        assert 'FD002' in registry.subsets
        assert 'FD003' in registry.subsets
        assert 'FD004' in registry.subsets
    
    def test_registry_subset_info(self):
        """Test registry provides correct subset information."""
        registry = DatasetRegistry()
        fd001_info = registry.get_subset_info('FD001')
        
        assert fd001_info is not None
        assert 'train_file' in fd001_info
        assert 'test_file' in fd001_info
        assert 'rul_file' in fd001_info
        assert 'n_engines' in fd001_info


class TestDatasetManagerSynthetic:
    """Test synthetic dataset generation."""
    
    def test_synthetic_dataset_basic_shape(self):
        """Test synthetic dataset produces correct shape."""
        dm = DatasetManager()
        X, y = dm.synthetic_dataset(n_engines=3, cycles_per_engine=50)
        
        # Verify shapes
        assert X.shape[0] > 0, "X should have samples"
        assert X.shape[1] == 17, f"X should have 17 features, got {X.shape[1]}"
        assert y.shape[0] == X.shape[0], "y should match X row count"
    
    def test_synthetic_dataset_feature_count(self):
        """Test synthetic dataset has exactly 17 features (3 op_settings + 14 sensors)."""
        dm = DatasetManager()
        X, y = dm.synthetic_dataset(n_engines=5)
        
        assert X.shape[1] == 17
        assert not np.isnan(X).any(), "X should not contain NaN"
        assert not np.isinf(X).any(), "X should not contain Inf"
    
    def test_synthetic_dataset_rul_values(self):
        """Test synthetic RUL values are positive and reasonable."""
        dm = DatasetManager()
        X, y = dm.synthetic_dataset(n_engines=5)
        
        # RUL should be positive and less than 200 cycles
        assert np.all(y > 0), f"All RUL values should be > 0, got min: {y.min()}"
        assert np.all(y < 200), f"RUL values should be < 200, got max: {y.max()}"
        assert y.dtype in [np.float32, np.float64, float], "RUL should be numeric"
    
    def test_synthetic_dataset_reproducibility(self):
        """Test synthetic dataset with seed produces reproducible results."""
        dm = DatasetManager()
        
        X1, y1 = dm.synthetic_dataset(n_engines=3, seed=42)
        X2, y2 = dm.synthetic_dataset(n_engines=3, seed=42)
        
        assert np.allclose(X1, X2), "Same seed should produce same data"
        assert np.allclose(y1, y2), "Same seed should produce same RUL"
    
    def test_synthetic_dataset_feature_ranges(self):
        """Test synthetic features are in reasonable ranges."""
        dm = DatasetManager()
        X, y = dm.synthetic_dataset(n_engines=10)
        
        # Operating settings should be roughly in [0, 10]
        # Sensors should be roughly in [0, 100]
        assert X.min() >= -10, "Features should not be extremely negative"
        assert X.max() <= 200, "Features should not be extremely large"
    
    def test_synthetic_dataset_with_engine_ids(self):
        """Test synthetic dataset returns engine IDs when requested."""
        dm = DatasetManager()
        X, y, engine_ids = dm.synthetic_dataset(n_engines=5, return_engine_ids=True)
        
        assert engine_ids is not None
        assert len(engine_ids) == X.shape[0]
        assert np.unique(engine_ids).shape[0] <= 5  # At most 5 engines


class TestDatasetManagerLoading:
    """Test real dataset loading functionality."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory with sample C-MAPSS data."""
        temp_dir = tempfile.mkdtemp()
        
        # Create train file
        train_data = []
        for engine_id in range(1, 4):
            n_cycles = 10 + engine_id * 2
            for cycle in range(1, n_cycles + 1):
                row = [engine_id, cycle] + [50 + np.random.randn()*5 for _ in range(17)]
                train_data.append(row)
        
        train_df = pd.DataFrame(train_data)
        train_df.to_csv(Path(temp_dir) / 'train_FD001.txt', sep=' ', header=False, index=False)
        
        # Create RUL file
        rul_data = {}
        for engine_id in range(1, 4):
            rul_data[engine_id] = 10 + engine_id * 2  # max cycles
        
        rul_lines = [str(rul) for rul in rul_data.values()]
        Path(temp_dir).joinpath('RUL_FD001.txt').write_text('\n'.join(rul_lines))
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_load_synthetic_data_default(self):
        """Test loading synthetic data by default."""
        dm = DatasetManager()
        X, y = dm.load('FD001', use_synthetic=True)
        
        assert X.shape[1] == 17
        assert len(y) == len(X)
        assert np.all(y > 0)
    
    def test_load_returns_numpy_arrays(self):
        """Test load returns numpy arrays, not DataFrames."""
        dm = DatasetManager()
        X, y = dm.load('FD001', use_synthetic=True)
        
        assert isinstance(X, np.ndarray), f"X should be ndarray, got {type(X)}"
        assert isinstance(y, np.ndarray), f"y should be ndarray, got {type(y)}"


class TestDatasetManagerValidation:
    """Test data validation functionality."""
    
    def test_validate_data_shape_correct(self):
        """Test validate_data with correct shape passes."""
        dm = DatasetManager()
        X = np.random.randn(100, 17)
        y = np.random.rand(100) * 100
        
        # Should not raise
        dm.validate_data(X, y)
    
    def test_validate_data_shape_mismatch(self):
        """Test validate_data rejects mismatched shapes."""
        dm = DatasetManager()
        X = np.random.randn(100, 17)
        y = np.random.rand(50) * 100  # Mismatch
        
        with pytest.raises(ValueError, match="shape mismatch"):
            dm.validate_data(X, y)
    
    def test_validate_data_wrong_feature_count(self):
        """Test validate_data rejects wrong feature count."""
        dm = DatasetManager()
        X = np.random.randn(100, 18)  # Should be 17
        y = np.random.rand(100) * 100
        
        with pytest.raises(ValueError, match="feature count|shape"):
            dm.validate_data(X, y)
    
    def test_validate_data_with_nan(self):
        """Test validate_data rejects NaN values."""
        dm = DatasetManager()
        X = np.random.randn(100, 17)
        X[0, 0] = np.nan
        y = np.random.rand(100) * 100
        
        with pytest.raises(ValueError, match="NaN"):
            dm.validate_data(X, y)
    
    def test_validate_data_with_inf(self):
        """Test validate_data rejects Inf values."""
        dm = DatasetManager()
        X = np.random.randn(100, 17)
        X[0, 0] = np.inf
        y = np.random.rand(100) * 100
        
        with pytest.raises(ValueError, match="inf|infinite"):
            dm.validate_data(X, y)
    
    def test_validate_data_with_negative_y(self):
        """Test validate_data rejects negative RUL values."""
        dm = DatasetManager()
        X = np.random.randn(100, 17)
        y = np.random.rand(100) * 100
        y[0] = -1  # Negative RUL
        
        with pytest.raises(ValueError, match="RUL|negative|positive"):
            dm.validate_data(X, y)


class TestDatasetManagerCaching:
    """Test data caching mechanism."""
    
    def test_cache_synthetic_data(self):
        """Test caching works for synthetic data."""
        dm = DatasetManager()
        
        # First call
        X1, y1 = dm.load('FD001', use_synthetic=True)
        
        # Second call should come from cache
        X2, y2 = dm.load('FD001', use_synthetic=True)
        
        assert np.array_equal(X1, X2), "Cached data should be identical"
        assert np.array_equal(y1, y2), "Cached RUL should be identical"
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        dm = DatasetManager()
        
        dm.load('FD001', use_synthetic=True)
        assert dm.is_cached('FD001'), "Data should be in cache"
        
        dm.clear_cache('FD001')
        assert not dm.is_cached('FD001'), "Cache should be cleared"
    
    def test_cache_full_clear(self):
        """Test clearing entire cache."""
        dm = DatasetManager()
        
        dm.load('FD001', use_synthetic=True)
        dm.load('FD002', use_synthetic=True)
        
        dm.clear_cache()  # Clear all
        
        assert not dm.is_cached('FD001')
        assert not dm.is_cached('FD002')


class TestDatasetManagerIntegration:
    """Integration tests for DatasetManager."""
    
    def test_end_to_end_load_and_validate(self):
        """Test complete load and validate workflow."""
        dm = DatasetManager()
        
        # Load synthetic data
        X, y = dm.load('FD001', use_synthetic=True)
        
        # Validate
        dm.validate_data(X, y)
        
        # Verify properties
        assert X.shape[1] == 17
        assert len(y) == X.shape[0]
        assert np.all(y > 0)
    
    def test_load_all_subsets(self):
        """Test loading all available subsets."""
        dm = DatasetManager()
        
        for subset in ['FD001', 'FD002', 'FD003', 'FD004']:
            X, y = dm.load(subset, use_synthetic=True)
            assert X.shape[1] == 17
            assert len(y) == X.shape[0]
    
    def test_dataset_manager_initialization(self):
        """Test DatasetManager initializes correctly."""
        dm = DatasetManager()
        
        assert dm is not None
        assert hasattr(dm, 'load')
        assert hasattr(dm, 'validate_data')
        assert hasattr(dm, 'synthetic_dataset')
        assert hasattr(dm, 'clear_cache')
