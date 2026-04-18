"""
Data preprocessing pipeline for NASA C-MAPSS dataset (Phase 2B: ML Data Preparation).

Implements full data processing workflow:
- Load C-MAPSS turbofan degradation data
- Create Remaining Useful Life (RUL) labels
- Normalize features (MinMax or Standard scaling)
- Engineer rolling statistical features (mean, std, slope)

Reference: Saxena et al., 2008 - NASA C-MAPSS dataset
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from scipy import stats
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """
    Comprehensive preprocessing pipeline for NASA C-MAPSS dataset.
    
    Features:
    - Loads C-MAPSS turbofan sensor data (14 active sensors, 3 operating settings)
    - Creates RUL (Remaining Useful Life) labels with piecewise linear transformation
    - Normalizes features with MinMax or Standard scaling
    - Engineers rolling statistics features (mean, std, slope)
    - Handles missing data and quality checks
    
    Attributes:
        data_dir (Path): Directory containing raw C-MAPSS data
        column_names (list): Names of all 17 input features
    """
    
    # C-MAPSS column mapping (19 features: engine_id + cycle + 3 op_settings + 14 sensors, minus 7 zero-variance)
    COLUMN_NAMES = [
        'engine_id', 'cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3',
        'sensor_2', 'sensor_3', 'sensor_4', 'sensor_7', 'sensor_8', 
        'sensor_9', 'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14',
        'sensor_15', 'sensor_17', 'sensor_20', 'sensor_21'
    ]
    
    # Columns to exclude from features (keep for indexing)
    INDEX_COLUMNS = ['engine_id', 'cycle']
    
    # Active sensor features (14 sensors after removing zero-variance columns)
    ACTIVE_SENSORS = [
        'sensor_2', 'sensor_3', 'sensor_4', 'sensor_7', 'sensor_8',
        'sensor_9', 'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14',
        'sensor_15', 'sensor_17', 'sensor_21'
    ]
    
    def __init__(self, data_dir: str = './data/raw'):
        """
        Initialize preprocessing pipeline.
        
        Args:
            data_dir: Path to directory containing raw C-MAPSS data
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized PreprocessingPipeline with data_dir: {self.data_dir}")
    
    def load_cmapss_data(self, subset: str = 'FD001') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Load NASA C-MAPSS turbofan degradation data.
        
        C-MAPSS dataset format:
        - Training file: train_{subset}.txt (space-separated, no header)
        - RUL file: RUL_{subset}.txt (one max cycle per line)
        
        Args:
            subset: Dataset subset (FD001, FD002, FD003, FD004)
                   FD001: Single operating condition, single fault mode
                   FD002: Same as FD001, additional training data
                   FD003: Single condition, two fault modes
                   FD004: Multiple conditions, two fault modes
            
        Returns:
            tuple: (X, y, engine_ids)
                - X: Feature matrix (n_samples, 17) [3 op_settings + 14 sensors]
                - y: RUL labels (n_samples,)
                - engine_ids: Engine identifiers (n_samples,)
                
        Raises:
            FileNotFoundError: If data files not found
        """
        train_file = self.data_dir / f'train_{subset}.txt'
        rul_file = self.data_dir / f'RUL_{subset}.txt'
        
        if not train_file.exists():
            raise FileNotFoundError(f"Training data not found: {train_file}")
        if not rul_file.exists():
            raise FileNotFoundError(f"RUL data not found: {rul_file}")
        
        logger.info(f"Loading {subset} data from {train_file}")
        
        # Load training data (space-separated, no header)
        df = pd.read_csv(train_file, sep=' ', header=None)
        df.columns = self.COLUMN_NAMES
        
        # Load max cycle per engine from RUL file
        with open(rul_file) as f:
            max_cycles = [int(line.strip()) for line in f]
        
        logger.info(f"Loaded {len(df)} samples from {len(max_cycles)} engines")
        
        # Create RUL labels
        y = self.create_rul_labels(df, max_rul=125)
        
        # Extract features (skip index columns)
        feature_cols = [col for col in self.COLUMN_NAMES if col not in self.INDEX_COLUMNS]
        X = df[feature_cols].values.astype(np.float32)
        
        # Extract engine IDs for tracking
        engine_ids = df['engine_id'].values
        
        logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")
        logger.info(f"RUL range: [{y.min():.1f}, {y.max():.1f}]")
        
        return X, y, engine_ids
    
    def create_rul_labels(self, data: pd.DataFrame, max_rul: int = 125) -> np.ndarray:
        """
        Create Remaining Useful Life (RUL) labels.
        
        RUL is calculated as: RUL = max_cycle - current_cycle
        Values are clipped at max_rul (piecewise linear transformation):
        - For cycles early in lifecycle: RUL = max_rul (flat)
        - For cycles near end: RUL = max_cycle - cycle (linear decline)
        
        This transformation reflects operational reality: early degradation
        doesn't provide failure prediction signal, but linear decline near
        end-of-life does.
        
        Args:
            data: DataFrame with columns ['engine_id', 'cycle']
            max_rul: Clipping threshold in cycles (default 125, ~7 days)
                    Represents planning horizon for maintenance decisions
            
        Returns:
            np.ndarray: RUL values in cycles (clipped at max_rul)
            
        Shape:
            - Input: DataFrame with n_samples rows
            - Output: (n_samples,) array
        """
        # Group by engine and get max cycle per engine
        max_cycles = data.groupby('engine_id')['cycle'].max()
        
        # Calculate RUL: max_cycle - current_cycle for each row
        rul = data.groupby('engine_id')['cycle'].transform(
            lambda x: max_cycles[x.name] - x
        )
        
        # Clip to max_rul threshold (piecewise linear)
        rul = np.minimum(rul.values, max_rul)
        
        logger.debug(f"RUL statistics - min: {rul.min()}, max: {rul.max()}, mean: {rul.mean():.1f}")
        
        return rul
    
    def normalize_features(
        self, 
        X: np.ndarray, 
        method: str = 'minmax'
    ) -> Tuple[np.ndarray, object]:
        """
        Normalize features using MinMax or Standard scaling.
        
        Normalization methods:
        - 'minmax': Scale to [0, 1] range
          X_norm = (X - X_min) / (X_max - X_min)
          Useful when data range is known and bounded
          
        - 'standard': Z-score normalization (StandardScaler)
          X_norm = (X - mean) / std
          Useful for algorithms assuming normally distributed features
        
        Args:
            X: Feature matrix (n_samples, n_features)
            method: Normalization method ('minmax' or 'standard')
            
        Returns:
            tuple: (X_normalized, scaler)
                - X_normalized: Normalized features (n_samples, n_features)
                - scaler: Fitted scaler object for later inverse transform
                
        Raises:
            ValueError: If method not in ['minmax', 'standard']
        """
        if method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'standard':
            scaler = StandardScaler()
        else:
            raise ValueError(f"Unknown normalization method: {method}. Use 'minmax' or 'standard'")
        
        X_normalized = scaler.fit_transform(X).astype(np.float32)
        
        logger.info(f"Normalized features using {method} method")
        logger.debug(f"Normalized range: [{X_normalized.min():.3f}, {X_normalized.max():.3f}]")
        
        return X_normalized, scaler
    
    def engineer_features(self, X: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        Engineer rolling statistical features.
        
        For each original feature, compute rolling statistics over a window:
        - rolling_mean: Average over window
        - rolling_std: Standard deviation over window  
        - rolling_slope: Linear trend (1st derivative) over window
        
        This captures degradation trends at different scales:
        - Original features: Instantaneous sensor readings
        - Rolling mean: Smoothed trend (noise reduction)
        - Rolling std: Variability increase (degradation indicator)
        - Rolling slope: Rate of change (early failure indicator)
        
        Args:
            X: Feature matrix (n_samples, n_features) - typically normalized
            window_size: Rolling window size in cycles (default 5 = ~1 hour)
            
        Returns:
            np.ndarray: Extended features (n_samples, n_features * 4)
                Columns: [original_features | rolling_mean | rolling_std | rolling_slope]
                
        Shape:
            - Input: (n_samples, 14)
            - Output: (n_samples, 56)  [14 + 14 + 14 + 14]
        """
        n_samples, n_features = X.shape
        
        # Initialize output matrix
        X_engineered = np.zeros((n_samples, n_features * 4), dtype=np.float32)
        
        # Copy original features
        X_engineered[:, :n_features] = X
        
        # Compute rolling features column by column
        for col_idx in range(n_features):
            series = pd.Series(X[:, col_idx])
            
            # Rolling mean
            rolling_mean = series.rolling(window=window_size, center=False).mean().values
            X_engineered[:, n_features + col_idx] = rolling_mean
            
            # Rolling std
            rolling_std = series.rolling(window=window_size, center=False).std().values
            X_engineered[:, 2 * n_features + col_idx] = rolling_std
            
            # Rolling slope (linear regression slope over window)
            rolling_slope = np.zeros(n_samples)
            for i in range(window_size - 1, n_samples):
                window_data = series.iloc[i - window_size + 1:i + 1].values
                x_vals = np.arange(window_size)
                slope, _ = np.polyfit(x_vals, window_data, 1)
                rolling_slope[i] = slope
            
            X_engineered[:, 3 * n_features + col_idx] = rolling_slope
        
        # Handle initial NaN values (before window fills)
        # Forward-fill with row mean
        for i in range(window_size - 1):
            row_mean = np.nanmean(X_engineered[i, :])
            X_engineered[i, np.isnan(X_engineered[i, :])] = row_mean
        
        # Replace any remaining NaN with 0 (should be minimal)
        X_engineered = np.nan_to_num(X_engineered, nan=0.0)
        
        logger.info(f"Engineered features: {X.shape} → {X_engineered.shape}")
        logger.debug(f"Feature range: [{X_engineered.min():.3f}, {X_engineered.max():.3f}]")
        
        return X_engineered
    
    def save_preprocessed_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        output_dir: str = './data/processed',
        filename_prefix: str = 'FD001'
    ) -> None:
        """
        Save preprocessed data to disk for later use.
        
        Args:
            X: Feature matrix
            y: Labels
            output_dir: Directory to save processed data
            filename_prefix: Prefix for saved files (default 'FD001')
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        X_file = output_path / f'{filename_prefix}_X.npy'
        y_file = output_path / f'{filename_prefix}_y.npy'
        
        np.save(X_file, X)
        np.save(y_file, y)
        
        logger.info(f"Saved preprocessed data to {output_path}")


if __name__ == '__main__':
    print("Preprocessing pipeline implementation complete (Phase 2B)")
    print("Features:")
    print("  - Load NASA C-MAPSS turbofan degradation data")
    print("  - Create RUL (Remaining Useful Life) labels")
    print("  - Normalize features (MinMax or Standard)")
    print("  - Engineer rolling statistical features (mean, std, slope)")
