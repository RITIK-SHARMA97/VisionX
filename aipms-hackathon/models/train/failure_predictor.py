"""
FailurePredictor - XGBoost based failure prediction model.

Predicts whether an engine will fail within a 7-day (30-cycle) horizon using XGBoost.
Provides calibrated failure probabilities and SHAP feature attribution.
"""

import numpy as np
from pathlib import Path
import pickle
import logging
from typing import Tuple, List, Dict
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import shap

logger = logging.getLogger(__name__)


class FailurePredictor:
    """XGBoost based binary failure predictor."""
    
    def __init__(self,
                 max_depth: int = 5,
                 learning_rate: float = 0.05,
                 n_estimators: int = 300,
                 threshold: float = 0.5,
                 random_state: int = None,
                 scale_pos_weight: float = None):
        """Initialize FailurePredictor.
        
        Args:
            max_depth: Maximum tree depth
            learning_rate: Learning rate (shrinkage)
            n_estimators: Number of boosting rounds
            threshold: Classification threshold for failure prediction
            random_state: Random seed
            scale_pos_weight: Weight for positive class (computed automatically if None)
        """
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.n_estimators = n_estimators
        self.threshold = threshold
        self.random_state = random_state
        self.scale_pos_weight = scale_pos_weight
        
        self.model = None
        self.is_fitted_ = False
        self.explainer_ = None
        self.feature_names_ = None
        
        logger.info(f"FailurePredictor initialized: max_depth={max_depth}, "
                   f"lr={learning_rate}, n_est={n_estimators}")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'FailurePredictor':
        """Fit XGBoost model on training data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (0 or 1)
        
        Returns:
            self for method chaining
        """
        # Validate input
        if len(np.unique(y)) < 2:
            raise ValueError(f"Need at least 2 classes, got {len(np.unique(y))}")
        
        # Compute scale_pos_weight if not provided
        scale_pos_weight = self.scale_pos_weight
        if scale_pos_weight is None:
            n_neg = np.sum(y == 0)
            n_pos = np.sum(y == 1)
            if n_pos > 0:
                scale_pos_weight = n_neg / n_pos
            else:
                scale_pos_weight = 1.0
            logger.debug(f"Computed scale_pos_weight={scale_pos_weight:.2f} "
                        f"(neg={n_neg}, pos={n_pos})")
        
        # Create and train model
        params = {
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'scale_pos_weight': scale_pos_weight,
            'random_state': self.random_state,
            'tree_method': 'hist',
            'verbosity': 0,
        }
        
        # Create DMatrix
        dtrain = xgb.DMatrix(X, label=y)
        
        # Train
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.n_estimators,
            verbose_eval=False
        )
        
        self.is_fitted_ = True
        
        # Create SHAP explainer
        self.explainer_ = shap.TreeExplainer(self.model)
        self.feature_names_ = [f"feature_{i}" for i in range(X.shape[1])]
        
        logger.debug(f"Fitted FailurePredictor on {X.shape[0]} samples, "
                    f"{X.shape[1]} features")
        
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict failure probability.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Failure probabilities (n_samples,) in [0, 1]
        """
        if not self.is_fitted_:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if X.shape[0] == 0:
            return np.array([], dtype=np.float32)
        
        # Create DMatrix
        dtest = xgb.DMatrix(X)
        
        # Predict
        proba = self.model.predict(dtest)
        
        return proba.astype(np.float32)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict failure binary labels.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Binary labels (n_samples,) with values {0, 1}
        """
        proba = self.predict_proba(X)
        return (proba >= self.threshold).astype(int)
    
    def get_shap_values(self, X: np.ndarray) -> np.ndarray:
        """Compute SHAP values for samples.
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            SHAP values (n_samples, n_features)
        """
        if not self.is_fitted_:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Create DMatrix
        dtest = xgb.DMatrix(X)
        
        # Compute SHAP values
        shap_values = self.explainer_.shap_values(dtest)
        
        return shap_values.astype(np.float32)
    
    def get_top_features(self, X: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """Get top-k most important features for a sample.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            k: Number of top features
        
        Returns:
            List of (feature_index, avg_shap_value) tuples
        """
        shap_values = self.get_shap_values(X)
        
        # Compute average absolute SHAP value per feature
        avg_importance = np.abs(shap_values).mean(axis=0)
        
        # Get top-k indices
        top_indices = np.argsort(avg_importance)[-k:][::-1]
        
        # Return as list of (index, importance) tuples
        return [(int(idx), float(avg_importance[idx])) for idx in top_indices]
    
    def compute_metrics(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Compute evaluation metrics.
        
        Args:
            X: Test features
            y: True labels
        
        Returns:
            Dictionary with metrics: accuracy, precision, recall, f1, auc_roc
        """
        proba = self.predict_proba(X)
        preds = self.predict(X)
        
        metrics = {
            'accuracy': float(accuracy_score(y, preds)),
            'precision': float(precision_score(y, preds, zero_division=0)),
            'recall': float(recall_score(y, preds, zero_division=0)),
            'f1': float(f1_score(y, preds, zero_division=0)),
            'auc_roc': float(roc_auc_score(y, proba)),
        }
        
        return metrics
    
    def save(self, path: Path) -> None:
        """Save model to disk.
        
        Args:
            path: Path to save model
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_dict = {
            'model': self.model,
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'n_estimators': self.n_estimators,
            'threshold': self.threshold,
            'random_state': self.random_state,
            'scale_pos_weight': self.scale_pos_weight,
            'is_fitted_': self.is_fitted_,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_dict, f)
        
        logger.info(f"Saved FailurePredictor to {path}")
    
    def load(self, path: Path) -> None:
        """Load model from disk.
        
        Args:
            path: Path to model file
        """
        path = Path(path)
        
        with open(path, 'rb') as f:
            model_dict = pickle.load(f)
        
        self.model = model_dict['model']
        self.max_depth = model_dict['max_depth']
        self.learning_rate = model_dict['learning_rate']
        self.n_estimators = model_dict['n_estimators']
        self.threshold = model_dict['threshold']
        self.random_state = model_dict['random_state']
        self.scale_pos_weight = model_dict['scale_pos_weight']
        self.is_fitted_ = model_dict['is_fitted_']
        
        # Recreate explainer
        if self.is_fitted_:
            self.explainer_ = shap.TreeExplainer(self.model)
        
        logger.info(f"Loaded FailurePredictor from {path}")
