"""
AnomalyDetector - Isolation Forest based anomaly detection model.

Detects anomalies in high-dimensional sensor data using Isolation Forest.
Outputs calibrated anomaly scores (0-1) and labels (normal/warning/critical).
"""

import numpy as np
from pathlib import Path
import pickle
import logging
from sklearn.ensemble import IsolationForest
from typing import Tuple, Literal

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Isolation Forest based anomaly detector for sensor data."""
    
    def __init__(self,
                 n_estimators: int = 100,
                 contamination: float = 0.05,
                 threshold_warning: float = 0.40,
                 threshold_critical: float = 0.70,
                 random_state: int = None,
                 max_samples: int = 256):
        """Initialize AnomalyDetector.
        
        Args:
            n_estimators: Number of base estimators in ensemble
            contamination: Expected proportion of anomalies in training data
            threshold_warning: Anomaly score threshold for warning (0-1)
            threshold_critical: Anomaly score threshold for critical (0-1)
            random_state: Random seed for reproducibility
            max_samples: Max samples for fitting each base estimator
        """
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.random_state = random_state
        self.max_samples = max_samples
        
        # Initialize Isolation Forest
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            max_samples=max_samples,
        )
        
        # Calibration parameters (computed during fitting)
        self.score_min_ = None
        self.score_max_ = None
        self.is_fitted_ = False
        
        logger.info(f"AnomalyDetector initialized: n_est={n_estimators}, "
                   f"contamination={contamination}, "
                   f"thresholds=({threshold_warning:.2f}, {threshold_critical:.2f})")
    
    def fit(self, X: np.ndarray) -> 'AnomalyDetector':
        """Fit Isolation Forest on training data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            self for method chaining
        """
        # Fit model
        self.model.fit(X)
        
        # Calibrate scores on training data
        raw_scores = self.model.score_samples(X)
        self.score_min_ = raw_scores.min()
        self.score_max_ = raw_scores.max()
        
        self.is_fitted_ = True
        
        logger.debug(f"Fitted AnomalyDetector on {X.shape[0]} samples, "
                    f"score range: [{self.score_min_:.4f}, {self.score_max_:.4f}]")
        
        return self
    
    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly scores for samples.
        
        Returns calibrated scores in [0, 1] where:
        - 0 = normal (similar to training data)
        - 1 = highly anomalous (unlike training data)
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Anomaly scores (n_samples,) in [0, 1]
        """
        if not self.is_fitted_:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if X.shape[0] == 0:
            return np.array([], dtype=np.float32)
        
        # Get raw scores from Isolation Forest
        # Note: sklearn returns negative scores (lower = more anomalous)
        raw_scores = self.model.score_samples(X)
        
        # Calibrate to [0, 1]
        # Invert so higher score = more anomalous
        score_range = self.score_max_ - self.score_min_
        
        if score_range == 0:
            # All training samples had same score
            calibrated = np.zeros(len(raw_scores), dtype=np.float32)
        else:
            # Normalize to [0, 1]
            calibrated = (self.score_max_ - raw_scores) / score_range
            calibrated = np.clip(calibrated, 0, 1)
        
        return calibrated.astype(np.float32)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomaly labels.
        
        Returns labels based on thresholds:
        - 'normal': score < threshold_warning
        - 'warning': threshold_warning <= score < threshold_critical
        - 'critical': score >= threshold_critical
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Labels array (n_samples,) with values {'normal', 'warning', 'critical'}
        """
        scores = self.score_samples(X)
        
        labels = np.empty(len(scores), dtype=object)
        
        labels[scores < self.threshold_warning] = 'normal'
        labels[(scores >= self.threshold_warning) & (scores < self.threshold_critical)] = 'warning'
        labels[scores >= self.threshold_critical] = 'critical'
        
        return labels
    
    def predict_with_scores(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict labels and return scores.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Tuple of (labels, scores)
        """
        scores = self.score_samples(X)
        labels = self.predict(X)
        return labels, scores
    
    def save(self, path: Path) -> None:
        """Save model to disk.
        
        Args:
            path: Path to save model pickle
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_dict = {
            'model': self.model,
            'n_estimators': self.n_estimators,
            'contamination': self.contamination,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical,
            'random_state': self.random_state,
            'max_samples': self.max_samples,
            'score_min_': self.score_min_,
            'score_max_': self.score_max_,
            'is_fitted_': self.is_fitted_,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_dict, f)
        
        logger.info(f"Saved AnomalyDetector to {path}")
    
    def load(self, path: Path) -> None:
        """Load model from disk.
        
        Args:
            path: Path to model pickle
        """
        path = Path(path)
        
        with open(path, 'rb') as f:
            model_dict = pickle.load(f)
        
        self.model = model_dict['model']
        self.n_estimators = model_dict['n_estimators']
        self.contamination = model_dict['contamination']
        self.threshold_warning = model_dict['threshold_warning']
        self.threshold_critical = model_dict['threshold_critical']
        self.random_state = model_dict['random_state']
        self.max_samples = model_dict['max_samples']
        self.score_min_ = model_dict['score_min_']
        self.score_max_ = model_dict['score_max_']
        self.is_fitted_ = model_dict['is_fitted_']
        
        logger.info(f"Loaded AnomalyDetector from {path}")
