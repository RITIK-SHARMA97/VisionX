"""
RUL (Remaining Useful Life) Estimator using LSTM networks.

This module implements an LSTM-based regression model for predicting remaining
useful life cycles based on sequences of engineered sensor features. The model
can optionally provide uncertainty estimates through Monte Carlo dropout.

Architecture:
- Input: Sequences of engineered features (sequence_length, n_features)
- LSTM layers with dropout for regularization
- Dense output layer for RUL prediction
- Optional uncertainty quantification using dropout

Key features:
- Automatic sequence creation from time series data
- Configurable LSTM architecture
- Uncertainty quantification with Monte Carlo dropout
- Comprehensive metrics (MAE, RMSE, R²)
- Model persistence with save/load
- Reproducible training with random state control
"""

import numpy as np
import os
from typing import Tuple, Optional, Dict
from pathlib import Path

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class RULEstimator:
    """LSTM-based Remaining Useful Life (RUL) predictor."""

    def __init__(
        self,
        sequence_length: int = 30,
        feature_dim: int = 68,
        lstm_units: int = 64,
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 50,
        uncertainty_quantification: bool = False,
        random_state: Optional[int] = None,
        verbose: int = 0
    ):
        """
        Initialize RUL Estimator.

        Args:
            sequence_length: Number of time steps in each sequence (window size)
            feature_dim: Number of features per time step (default: 68 for AIPMS)
            lstm_units: Number of LSTM units in hidden layer
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for Adam optimizer
            batch_size: Training batch size
            epochs: Number of training epochs
            uncertainty_quantification: Whether to use MC dropout for uncertainty
            random_state: Random seed for reproducibility
            verbose: Verbosity level (0=silent, 1=progress, 2=per-epoch)
        """
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.uncertainty_quantification = uncertainty_quantification
        self.random_state = random_state
        self.verbose = verbose

        self.model = None
        self.is_fitted_ = False
        self.history = None
        self.dropout_model = None  # For MC dropout inference

        if random_state is not None:
            np.random.seed(random_state)
            tf.random.set_seed(random_state)

    def _create_sequences(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create overlapping sequences from time series data.

        Args:
            X: Input features (n_samples, n_features)
            y: Target RUL values (n_samples,)

        Returns:
            X_seq: Sequences (n_sequences, sequence_length, n_features)
            y_seq: Corresponding RUL values (n_sequences,)
        """
        n_samples = X.shape[0]
        n_sequences = n_samples - self.sequence_length + 1

        X_seq = np.zeros(
            (n_sequences, self.sequence_length, self.feature_dim),
            dtype=np.float32
        )
        y_seq = np.zeros(n_sequences, dtype=np.float32)

        for i in range(n_sequences):
            X_seq[i] = X[i:i + self.sequence_length]
            y_seq[i] = y[i + self.sequence_length - 1]

        return X_seq, y_seq

    def _build_model(self) -> keras.Model:
        """
        Build LSTM model architecture.

        Returns:
            Compiled Keras model
        """
        model = models.Sequential([
            layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            # First LSTM layer with dropout
            layers.LSTM(
                self.lstm_units,
                activation='relu',
                return_sequences=True
            ),
            layers.Dropout(self.dropout_rate),
            
            # Second LSTM layer
            layers.LSTM(
                self.lstm_units // 2,
                activation='relu',
                return_sequences=False
            ),
            layers.Dropout(self.dropout_rate),
            
            # Dense layers
            layers.Dense(self.lstm_units // 2, activation='relu'),
            layers.Dropout(self.dropout_rate),
            
            # Output layer (RUL prediction, must be positive)
            layers.Dense(1, activation='relu')
        ])

        optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae']
        )

        return model

    def _build_dropout_model(self) -> keras.Model:
        """
        Build model for MC dropout uncertainty estimation.
        Uses same weights as main model but keeps dropout active at test time.
        """
        if not self.uncertainty_quantification or self.model is None:
            return None

        # Create functional model that keeps dropout active
        inputs = keras.Input(shape=(self.sequence_length, self.feature_dim))
        x = inputs

        # Copy layers from main model but force training=True for dropout
        for layer in self.model.layers:
            if isinstance(layer, layers.Dropout):
                x = layer(x, training=True)
            else:
                x = layer(x)

        dropout_model = keras.Model(inputs=inputs, outputs=x)
        return dropout_model

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_split: float = 0.2,
        verbose: Optional[int] = None
    ) -> 'RULEstimator':
        """
        Train the LSTM model on sequence data.

        Args:
            X: Input features (n_samples, n_features)
            y: Target RUL values (n_samples,)
            validation_split: Fraction of data to use for validation
            verbose: Training verbosity (overrides self.verbose if provided)

        Returns:
            self for method chaining
        """
        if X.shape[1] != self.feature_dim:
            raise ValueError(
                f"Feature dimension mismatch: expected {self.feature_dim}, "
                f"got {X.shape[1]}"
            )

        # Create sequences
        X_seq, y_seq = self._create_sequences(X, y)

        if len(X_seq) == 0:
            raise ValueError(
                f"Not enough samples for sequence_length={self.sequence_length}. "
                f"Need at least {self.sequence_length} samples."
            )

        # Build and train model
        self.model = self._build_model()

        verb = verbose if verbose is not None else self.verbose

        self.history = self.model.fit(
            X_seq,
            y_seq,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=validation_split,
            verbose=verb
        )

        self.is_fitted_ = True

        # Build dropout model if uncertainty quantification enabled
        if self.uncertainty_quantification:
            self.dropout_model = self._build_dropout_model()

        return self

    def predict(
        self,
        X: np.ndarray,
        return_uncertainty: bool = False,
        n_mc_samples: int = 30
    ) -> np.ndarray:
        """
        Predict RUL for new data.

        Args:
            X: Input features (n_samples, n_features)
            return_uncertainty: Whether to return uncertainty estimates
            n_mc_samples: Number of MC dropout samples for uncertainty

        Returns:
            predictions: Predicted RUL values (n_sequences,)
            uncertainty: (optional) Standard deviation of predictions
        """
        if not self.is_fitted_ or self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")

        if len(X) == 0:
            return np.array([], dtype=np.float32)

        if X.shape[1] != self.feature_dim:
            raise ValueError(
                f"Feature dimension mismatch: expected {self.feature_dim}, "
                f"got {X.shape[1]}"
            )

        # Create sequences
        n_samples = X.shape[0]
        n_sequences = max(0, n_samples - self.sequence_length + 1)

        if n_sequences == 0:
            return np.array([], dtype=np.float32)

        X_seq = np.zeros(
            (n_sequences, self.sequence_length, self.feature_dim),
            dtype=np.float32
        )

        for i in range(n_sequences):
            X_seq[i] = X[i:i + self.sequence_length]

        # Get predictions
        preds = self.model.predict(X_seq, verbose=0).flatten()

        if not return_uncertainty or not self.uncertainty_quantification:
            return preds.astype(np.float32)

        # MC dropout for uncertainty
        if self.dropout_model is not None:
            mc_preds = np.array([
                self.dropout_model.predict(X_seq, verbose=0).flatten()
                for _ in range(n_mc_samples)
            ])
            uncertainty = np.std(mc_preds, axis=0)
        else:
            uncertainty = np.zeros_like(preds)

        return preds.astype(np.float32), uncertainty.astype(np.float32)

    def get_top_features(
        self,
        X: np.ndarray,
        k: int = 5
    ) -> list:
        """
        Get top-k important features (using layer attention weights).

        Args:
            X: Input features
            k: Number of top features to return

        Returns:
            List of (feature_index, importance_score) tuples
        """
        if not self.is_fitted_:
            raise ValueError("Model not fitted. Call fit() first.")

        # Simple importance: sum of LSTM weights for each feature
        lstm_layer = self.model.layers[0]
        weights = lstm_layer.get_weights()[0]  # Shape: (n_features, 4*lstm_units)

        # Sum absolute weights across LSTM gates
        feature_importance = np.abs(weights).sum(axis=1)

        # Get top k
        top_indices = np.argsort(-feature_importance)[:k]
        top_features = [
            (int(idx), float(feature_importance[idx]))
            for idx in top_indices
        ]

        return top_features

    def compute_metrics(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute regression metrics on test data.

        Args:
            X: Input features
            y: Ground truth RUL values

        Returns:
            Dictionary with metrics (MAE, RMSE, R²)
        """
        if not self.is_fitted_:
            raise ValueError("Model not fitted. Call fit() first.")

        preds = self.predict(X)

        # Align y with predictions (account for sequence windowing)
        y_aligned = y[self.sequence_length - 1:self.sequence_length - 1 + len(preds)]

        mae = float(mean_absolute_error(y_aligned, preds))
        rmse = float(np.sqrt(mean_squared_error(y_aligned, preds)))
        r2 = float(r2_score(y_aligned, preds))

        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2
        }

    def save(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Directory path to save model
        """
        if not self.is_fitted_:
            raise ValueError("Cannot save unfitted model. Call fit() first.")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save model weights
        self.model.save(str(path / 'model.keras'))

        # Save configuration
        config = {
            'sequence_length': self.sequence_length,
            'feature_dim': self.feature_dim,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'uncertainty_quantification': self.uncertainty_quantification,
        }

        import json
        with open(path / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def load(path: str) -> 'RULEstimator':
        """
        Load model from disk.

        Args:
            path: Directory path with saved model

        Returns:
            RULEstimator instance with loaded weights
        """
        path = Path(path)

        # Load configuration
        import json
        with open(path / 'config.json', 'r') as f:
            config = json.load(f)

        # Create new instance
        rul = RULEstimator(**config)

        # Load model
        rul.model = keras.models.load_model(str(path / 'model.keras'))
        rul.is_fitted_ = True

        # Rebuild dropout model if needed
        if rul.uncertainty_quantification:
            rul.dropout_model = rul._build_dropout_model()

        return rul
