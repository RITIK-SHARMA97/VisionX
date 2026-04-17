"""
Data preprocessing stubs for Phase 2B (ML preparation)
"""
import numpy as np
import pandas as pd
from pathlib import Path

class PreprocessingPipeline:
    """
    Preprocessing pipeline for NASA C-MAPSS dataset.
    To be implemented in Phase 2B (ML Data Preparation).
    """
    
    def __init__(self, data_dir: str = './data/raw'):
        self.data_dir = Path(data_dir)
    
    def load_cmapss_data(self, subset: str = 'FD001'):
        """
        Load NASA C-MAPSS turbofan degradation data.
        
        Args:
            subset: FD001, FD002, FD003, FD004
            
        Returns:
            tuple: (X, y) training data
        """
        # To be implemented in Phase 2B
        raise NotImplementedError("Loading C-MAPSS data in Phase 2B")
    
    def create_rul_labels(self, data: pd.DataFrame, max_rul: int = 125):
        """
        Create Remaining Useful Life (RUL) labels.
        RUL = max_cycle - current_cycle (clipped at max_rul).
        
        Args:
            data: DataFrame with columns [engine_id, cycle]
            max_rul: Clipping threshold (default 125 cycles)
            
        Returns:
            Series: RUL values
        """
        # To be implemented in Phase 2B
        raise NotImplementedError("RUL labeling in Phase 2B")
    
    def normalize_features(self, X: np.ndarray, method: str = 'minmax'):
        """
        Normalize features using MinMaxScaler or StandardScaler.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            method: 'minmax' or 'standard'
            
        Returns:
            tuple: (X_normalized, scaler) for later transform
        """
        # To be implemented in Phase 2B
        raise NotImplementedError("Feature normalization in Phase 2B")
    
    def engineer_features(self, X: np.ndarray, window_size: int = 5):
        """
        Engineer rolling statistics features (mean, std, slope).
        
        Args:
            X: Feature matrix
            window_size: Rolling window size (default 5 cycles)
            
        Returns:
            np.ndarray: Extended feature matrix with rolling statistics
        """
        # To be implemented in Phase 2B
        raise NotImplementedError("Feature engineering in Phase 2B")


if __name__ == '__main__':
    print("Preprocessing pipeline stubs created.")
    print("Implementation scheduled for Phase 2B (ML Data Preparation)")
