"""
DatasetManager - Unified data loading for NASA C-MAPSS datasets.

Provides:
- Synthetic dataset generation for local testing
- Real dataset loading (C-MAPSS FD001-FD004)
- Data validation and quality checks
- Caching mechanism to avoid re-downloading
- Dataset registry with metadata
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatasetRegistry:
    """Registry of available C-MAPSS datasets."""
    
    def __init__(self):
        """Initialize dataset registry with known subsets."""
        self.subsets = {
            'FD001': {
                'description': 'Single operating condition, single fault mode',
                'n_engines': 100,
                'train_file': 'train_FD001.txt',
                'test_file': 'test_FD001.txt',
                'rul_file': 'RUL_FD001.txt',
            },
            'FD002': {
                'description': 'Six operating conditions, single fault mode',
                'n_engines': 260,
                'train_file': 'train_FD002.txt',
                'test_file': 'test_FD002.txt',
                'rul_file': 'RUL_FD002.txt',
            },
            'FD003': {
                'description': 'Single operating condition, two fault modes',
                'n_engines': 100,
                'train_file': 'train_FD003.txt',
                'test_file': 'test_FD003.txt',
                'rul_file': 'RUL_FD003.txt',
            },
            'FD004': {
                'description': 'Six operating conditions, two fault modes',
                'n_engines': 249,
                'train_file': 'train_FD004.txt',
                'test_file': 'test_FD004.txt',
                'rul_file': 'RUL_FD004.txt',
            }
        }
    
    def get_subset_info(self, subset: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific subset."""
        return self.subsets.get(subset)
    
    def list_subsets(self) -> list:
        """List all available subsets."""
        return list(self.subsets.keys())


class DatasetManager:
    """Unified dataset manager for C-MAPSS data.
    
    Handles:
    - Synthetic dataset generation
    - Real dataset loading
    - Data validation
    - Caching
    """
    
    # Column names for C-MAPSS data (19 total: engine_id + cycle + 3 op_settings + 14 sensors)
    # Index columns: engine_id, cycle
    # Feature columns: 17 (3 op_settings + 14 active sensors)
    COLUMN_NAMES = [
        'engine_id', 'cycle',
        'op_setting_1', 'op_setting_2', 'op_setting_3',
        'sensor_2', 'sensor_3', 'sensor_4', 'sensor_7', 'sensor_8', 'sensor_9',
        'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15', 'sensor_17', 'sensor_20', 'sensor_21'
    ]
    
    INDEX_COLUMNS = ['engine_id', 'cycle']
    FEATURE_COLUMNS = COLUMN_NAMES[2:]  # All except engine_id and cycle
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize DatasetManager.
        
        Args:
            data_dir: Path to data directory (default: ./data/raw)
        """
        self.data_dir = Path(data_dir) if data_dir else Path('./data/raw')
        self.registry = DatasetRegistry()
        self._cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        
        logger.info(f"DatasetManager initialized with data_dir: {self.data_dir}")
    
    def load(self, subset: str = 'FD001', use_synthetic: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Load dataset.
        
        Args:
            subset: Dataset subset (FD001, FD002, FD003, FD004)
            use_synthetic: Use synthetic data if real data not found
        
        Returns:
            Tuple of (X, y) where:
                X: Feature matrix (n_samples, 17)
                y: RUL labels (n_samples,)
        """
        # Check cache first
        if subset in self._cache:
            logger.debug(f"Loading {subset} from cache")
            return self._cache[subset]
        
        # Try real data
        if self.data_dir.exists():
            info = self.registry.get_subset_info(subset)
            if info:
                train_file = self.data_dir / info['train_file']
                rul_file = self.data_dir / info['rul_file']
                
                if train_file.exists() and rul_file.exists():
                    try:
                        X, y = self._load_cmapss_files(train_file, rul_file)
                        self._cache[subset] = (X, y)
                        logger.info(f"Loaded real data for {subset}: X.shape={X.shape}, y.shape={y.shape}")
                        return X, y
                    except Exception as e:
                        logger.warning(f"Failed to load real data for {subset}: {e}")
        
        # Fallback to synthetic
        if use_synthetic:
            logger.info(f"Using synthetic data for {subset}")
            X, y = self.synthetic_dataset()
            self._cache[subset] = (X, y)
            return X, y
        
        raise FileNotFoundError(f"Dataset {subset} not found and use_synthetic=False")
    
    def _load_cmapss_files(self, train_file: Path, rul_file: Path) -> Tuple[np.ndarray, np.ndarray]:
        """Load C-MAPSS training and RUL files.
        
        Args:
            train_file: Path to training data file
            rul_file: Path to RUL file
        
        Returns:
            Tuple of (X, y)
        """
        # Load training data
        df_train = pd.read_csv(train_file, sep=' ', header=None, names=self.COLUMN_NAMES)
        
        # Load RUL values
        rul_values = pd.read_csv(rul_file, header=None)[0].values
        
        # Extract features (exclude engine_id and cycle)
        X = df_train[self.FEATURE_COLUMNS].values
        
        # Create RUL labels
        y_list = []
        for engine_id in df_train['engine_id'].unique():
            engine_data = df_train[df_train['engine_id'] == engine_id]
            max_cycle = engine_data['cycle'].max()
            rul_at_max = rul_values[engine_id - 1]  # 0-indexed
            
            for _, row in engine_data.iterrows():
                rul = max_cycle - row['cycle'] + rul_at_max
                y_list.append(rul)
        
        y = np.array(y_list, dtype=np.float32)
        
        # Validate loaded data
        self.validate_data(X, y)
        
        return X.astype(np.float32), y
    
    def synthetic_dataset(self, 
                          n_engines: int = 10,
                          cycles_per_engine: int = 50,
                          return_engine_ids: bool = False,
                          seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic C-MAPSS dataset.
        
        Args:
            n_engines: Number of synthetic engines
            cycles_per_engine: Approximate cycles per engine
            return_engine_ids: Whether to return engine IDs
            seed: Random seed for reproducibility
        
        Returns:
            Tuple of (X, y) or (X, y, engine_ids) if return_engine_ids=True
            where X has shape (n_samples, 17) and y has shape (n_samples,)
        """
        if seed is not None:
            np.random.seed(seed)
        
        X_list = []
        y_list = []
        engine_ids_list = []
        
        for engine_id in range(1, n_engines + 1):
            # Vary cycles slightly per engine
            n_cycles = cycles_per_engine + np.random.randint(-10, 10)
            max_cycle = n_cycles
            
            for cycle in range(1, n_cycles + 1):
                # Generate 17 features
                # 3 operating settings: roughly [0, 10]
                op_settings = np.random.uniform(0, 10, 3)
                
                # 14 sensor readings: roughly [30, 70] with some drift
                cycle_fraction = cycle / max_cycle
                sensor_base = 50 + 10 * cycle_fraction  # Degradation
                sensors = np.random.normal(sensor_base, 5, 14)
                sensors = np.clip(sensors, 20, 100)  # Clip to reasonable range
                
                # Combine features
                features = np.concatenate([op_settings, sensors])
                X_list.append(features)
                
                # RUL = remaining cycles until max_cycle, with minimum of 1
                rul = max(max_cycle - cycle + 1, 1)  # Ensure RUL >= 1
                y_list.append(rul)
                
                engine_ids_list.append(engine_id)
        
        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32)
        
        # Validate
        self.validate_data(X, y)
        
        if return_engine_ids:
            engine_ids = np.array(engine_ids_list, dtype=np.int32)
            return X, y, engine_ids
        
        return X, y
    
    def validate_data(self, X: np.ndarray, y: np.ndarray) -> None:
        """Validate loaded data.
        
        Args:
            X: Feature matrix
            y: RUL labels
        
        Raises:
            ValueError: If data is invalid
        """
        # Check shapes
        if X.ndim != 2:
            raise ValueError(f"X should be 2D, got shape {X.shape}")
        
        if y.ndim != 1:
            raise ValueError(f"y should be 1D, got shape {y.shape}")
        
        if X.shape[0] != y.shape[0]:
            raise ValueError(f"shape mismatch: X has {X.shape[0]} samples, y has {y.shape[0]}")
        
        if X.shape[1] != 17:
            raise ValueError(f"feature count mismatch: expected 17, got {X.shape[1]}")
        
        # Check for NaN and Inf
        if np.isnan(X).any():
            raise ValueError("X contains NaN values")
        
        if np.isinf(X).any():
            raise ValueError("X contains inf values")
        
        if np.isnan(y).any():
            raise ValueError("y contains NaN values")
        
        if np.isinf(y).any():
            raise ValueError("y contains infinite values")
        
        # Check RUL values are non-negative
        if np.any(y < 0):
            raise ValueError(f"RUL values must be non-negative, found min: {y.min()}")
        
        logger.debug(f"Data validation passed: X.shape={X.shape}, y.shape={y.shape}")
    
    def is_cached(self, subset: str) -> bool:
        """Check if dataset is in cache.
        
        Args:
            subset: Dataset subset name
        
        Returns:
            True if cached
        """
        return subset in self._cache
    
    def clear_cache(self, subset: Optional[str] = None) -> None:
        """Clear cache.
        
        Args:
            subset: Specific subset to clear, or None to clear all
        """
        if subset is None:
            self._cache.clear()
            logger.info("Cleared entire cache")
        else:
            if subset in self._cache:
                del self._cache[subset]
                logger.info(f"Cleared cache for {subset}")
    
    def get_subset_info(self, subset: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a dataset subset.
        
        Args:
            subset: Dataset subset name
        
        Returns:
            Dictionary with subset metadata or None
        """
        return self.registry.get_subset_info(subset)
