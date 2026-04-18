"""
FeatureEngineer - Data preprocessing and feature engineering pipeline.

Provides:
- Min-Max normalization with inverse transform
- Rolling statistics feature engineering (mean, std, slope)
- Train/val/test splitting with leakage prevention
- RUL target transformations
- Scaler persistence (save/load)
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import pickle
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class RULScaler:
    """Scaler for RUL target variable."""
    
    def __init__(self, rul_max: float = 125.0):
        """Initialize RUL scaler.
        
        Args:
            rul_max: Maximum RUL value (will be clipped to this)
        """
        self.rul_max = rul_max
    
    def clip(self, y: np.ndarray) -> np.ndarray:
        """Clip RUL values to maximum.
        
        Args:
            y: RUL values
        
        Returns:
            Clipped RUL values
        """
        return np.minimum(y, self.rul_max)


class FeatureEngineer:
    """Data preprocessing and feature engineering pipeline."""
    
    # Raw feature columns (after removing engine_id and cycle)
    N_RAW_FEATURES = 17  # 3 op_settings + 14 sensors
    
    def __init__(self, window_size: int = 5, rul_max: float = 125.0):
        """Initialize FeatureEngineer.
        
        Args:
            window_size: Window size for rolling statistics
            rul_max: Maximum RUL value for clipping
        """
        self.window_size = window_size
        self.rul_max = rul_max
        self.rul_scaler = RULScaler(rul_max)
        
        # Scalers for each feature (fitted later)
        self.scaler_min = None
        self.scaler_max = None
        self.scaler_range = None
        self.scaler_fit = False
        
        logger.info(f"FeatureEngineer initialized: window_size={window_size}, rul_max={rul_max}")
    
    def normalize(self, X: np.ndarray) -> np.ndarray:
        """Min-Max normalize features.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Normalized features in [0, 1] range
        """
        if not self.scaler_fit:
            # Fit on this data
            self.scaler_min = X.min(axis=0)
            self.scaler_max = X.max(axis=0)
            self.scaler_range = self.scaler_max - self.scaler_min
            
            # Avoid division by zero
            self.scaler_range[self.scaler_range == 0] = 1.0
            
            self.scaler_fit = True
            logger.debug(f"Fitted scaler on {X.shape[0]} samples")
        
        # Normalize
        X_norm = (X - self.scaler_min) / self.scaler_range
        
        # Clip to [0, 1] to handle floating point errors
        X_norm = np.clip(X_norm, 0, 1)
        
        return X_norm.astype(np.float32)
    
    def inverse_normalize(self, X_norm: np.ndarray) -> np.ndarray:
        """Inverse Min-Max normalization.
        
        Args:
            X_norm: Normalized features
        
        Returns:
            Original scale features
        """
        if not self.scaler_fit:
            raise ValueError("Scaler not fitted. Call normalize() first.")
        
        X = X_norm * self.scaler_range + self.scaler_min
        return X.astype(np.float32)
    
    def compute_rolling_features(self, X: np.ndarray) -> np.ndarray:
        """Compute rolling window statistics.
        
        For each feature, computes:
        - Rolling mean
        - Rolling standard deviation
        - Rolling slope (linear regression)
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Augmented features (n_samples - window_size + 1, n_features * 4)
            Contains: [original_features, rolling_mean, rolling_std, rolling_slope]
        """
        n_samples, n_features = X.shape
        
        # Initialize output array
        # We'll drop first window_size-1 rows, so output has n_samples - window_size + 1 rows
        X_aug = []
        
        for i in range(self.window_size - 1, n_samples):
            window = X[i - self.window_size + 1:i + 1, :]  # (window_size, n_features)
            
            # Original features
            row = X[i, :].copy()
            
            # Rolling mean
            row_mean = window.mean(axis=0)
            row = np.concatenate([row, row_mean])
            
            # Rolling std
            row_std = window.std(axis=0)
            row = np.concatenate([row, row_std])
            
            # Rolling slope (linear regression)
            row_slope = np.zeros(n_features)
            for feat_idx in range(n_features):
                window_feat = window[:, feat_idx]
                t = np.arange(len(window_feat))
                
                # Linear regression: y = slope * t + intercept
                if window_feat.std() > 0:
                    slope = np.polyfit(t, window_feat, 1)[0]
                else:
                    slope = 0
                
                row_slope[feat_idx] = slope
            
            row = np.concatenate([row, row_slope])
            X_aug.append(row)
        
        X_aug = np.array(X_aug, dtype=np.float32)
        
        logger.debug(f"Rolling features: {X.shape} -> {X_aug.shape}")
        
        return X_aug
    
    def clip_rul(self, y: np.ndarray, rul_max: Optional[float] = None) -> np.ndarray:
        """Clip RUL values to maximum.
        
        Args:
            y: RUL values
            rul_max: Maximum value (default: self.rul_max)
        
        Returns:
            Clipped RUL values
        """
        if rul_max is None:
            rul_max = self.rul_max
        
        return np.minimum(y, rul_max).astype(np.float32)
    
    def create_binary_failure_labels(self, y: np.ndarray, horizon: int = 30) -> np.ndarray:
        """Create binary failure labels: 1 if RUL <= horizon, 0 otherwise.
        
        Args:
            y: RUL values
            horizon: Failure prediction horizon in cycles
        
        Returns:
            Binary labels (0 or 1)
        """
        labels = (y <= horizon).astype(np.int32)
        return labels
    
    def train_val_test_split(self,
                              X: np.ndarray,
                              y: np.ndarray,
                              train_frac: float = 0.6,
                              val_frac: float = 0.2,
                              seed: Optional[int] = None) -> Tuple[
                                  np.ndarray, np.ndarray, np.ndarray,
                                  np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train/val/test sets.
        
        Splits by random indices to prevent data leakage.
        
        Args:
            X: Feature matrix
            y: Labels
            train_frac: Fraction for training
            val_frac: Fraction for validation
            seed: Random seed
        
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        if seed is not None:
            np.random.seed(seed)
        
        n_samples = X.shape[0]
        
        # Generate random indices
        indices = np.random.permutation(n_samples)
        
        # Split indices
        n_train = int(n_samples * train_frac)
        n_val = int(n_samples * val_frac)
        
        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]
        
        # Split data
        X_train = X[train_indices]
        X_val = X[val_indices]
        X_test = X[test_indices]
        
        y_train = y[train_indices]
        y_val = y[val_indices]
        y_test = y[test_indices]
        
        logger.info(f"Train/val/test split: {X_train.shape[0]} / {X_val.shape[0]} / {X_test.shape[0]}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_scaler(self, path: Path) -> None:
        """Save fitted scaler to disk.
        
        Args:
            path: Path to save scaler pickle
        """
        if not self.scaler_fit:
            raise ValueError("Scaler not fitted. Call normalize() first.")
        
        scaler_dict = {
            'scaler_min': self.scaler_min,
            'scaler_max': self.scaler_max,
            'scaler_range': self.scaler_range,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(scaler_dict, f)
        
        logger.info(f"Saved scaler to {path}")
    
    def load_scaler(self, path: Path) -> None:
        """Load fitted scaler from disk.
        
        Args:
            path: Path to scaler pickle
        """
        with open(path, 'rb') as f:
            scaler_dict = pickle.load(f)
        
        self.scaler_min = scaler_dict['scaler_min']
        self.scaler_max = scaler_dict['scaler_max']
        self.scaler_range = scaler_dict['scaler_range']
        self.scaler_fit = True
        
        logger.info(f"Loaded scaler from {path}")
    
    def process(self, X: np.ndarray) -> np.ndarray:
        """Complete preprocessing pipeline.
        
        Args:
            X: Raw features
        
        Returns:
            Preprocessed features
        """
        # Compute rolling features
        X = self.compute_rolling_features(X)
        
        # Normalize
        X = self.normalize(X)
        
        return X
    
    def get_feature_count(self) -> int:
        """Get number of features after engineering.
        
        Returns:
            Number of features (raw + mean + std + slope)
        """
        # Original features + rolling mean + rolling std + rolling slope
        return self.N_RAW_FEATURES * 4
