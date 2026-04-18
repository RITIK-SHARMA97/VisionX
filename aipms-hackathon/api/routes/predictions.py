"""
API Routes for ML Model Inference

Provides REST endpoints for:
- Single prediction inference (anomaly, failure, RUL)
- Ensemble predictions (all 3 models)
- Batch processing
- Model status and management

Each endpoint handles:
1. Request validation (Pydantic schemas)
2. Model loading (lazy initialization with caching)
3. Feature normalization (MinMaxScaler)
4. Inference execution (< 100ms target)
5. Response formatting (standardized JSON)
6. Error handling (meaningful error messages)
"""

import logging
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
import numpy as np
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import pickle
import joblib

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Data Models
# ============================================================================

class PredictionRequest(BaseModel):
    """Request model for single prediction."""
    features: List[float] = Field(..., description="11-dimensional feature vector")
    equipment_id: Optional[str] = Field(default="unknown", description="Equipment identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [0.45, 52.3, 1.2, 2100, 18.5, 0.052, 0.048, 0.051, 0.049, 0.050, 0.051],
                "equipment_id": "EXC-01"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""
    batch: List[List[float]] = Field(..., description="Batch of feature vectors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch": [
                    [0.45, 52.3, 1.2, 2100, 18.5, 0.052, 0.048, 0.051, 0.049, 0.050, 0.051],
                    [0.50, 55.1, 1.3, 2150, 19.2, 0.055, 0.050, 0.052, 0.051, 0.051, 0.052]
                ]
            }
        }


class EnsembleRequest(BaseModel):
    """Request model for ensemble predictions."""
    features: List[float] = Field(..., description="11-dimensional feature vector")
    equipment_id: Optional[str] = Field(default="unknown", description="Equipment identifier")
    include_shap: bool = Field(default=False, description="Include SHAP feature importance")


class MetricsRequest(BaseModel):
    """Request model for metrics computation."""
    X: List[List[float]] = Field(..., description="Feature matrix")
    y: List[float] = Field(..., description="Target labels")
    
    class Config:
        json_schema_extra = {
            "example": {
                "X": [[0.45, 52.3, 1.2, 2100, 18.5, 0.052, 0.048, 0.051, 0.049, 0.050, 0.051]],
                "y": [1.0]
            }
        }


class SaveModelsRequest(BaseModel):
    """Request model for saving models."""
    path: str = Field(default="models/saved", description="Path to save models")
    
    class Config:
        json_schema_extra = {
            "example": {"path": "models/saved"}
        }


class RetrainModelRequest(BaseModel):
    """Request model for retraining."""
    model_type: str = Field(..., description="Model to retrain: 'anomaly', 'failure', or 'rul'")
    contamination: Optional[float] = Field(default=0.05, description="Contamination for anomaly detector")
    
    class Config:
        json_schema_extra = {
            "example": {"model_type": "anomaly", "contamination": 0.05}
        }


class PredictionResponse(BaseModel):
    """Standard response model for predictions."""
    status: str
    data: Dict[str, Any]
    timestamp: str
    latency_ms: float


# ============================================================================
# Model Cache & Initialization
# ============================================================================

class MetricsRequest(BaseModel):
    """Request model for computing RUL metrics."""
    X: List[List[float]]
    y: List[float]
    
    class Config:
        schema_extra = {
            "example": {
                "X": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                "y": [10.0, 5.0]
            }
        }


class SaveModelsRequest(BaseModel):
    """Request model for saving models to disk."""
    path: str = "./models/saved"
    
    class Config:
        schema_extra = {
            "example": {
                "path": "./models/saved"
            }
        }


class RetrainModelRequest(BaseModel):
    """Request model for retraining a model."""
    model_name: str  # 'anomaly', 'failure', 'rul'
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "rul",
                "epochs": 10,
                "batch_size": 32,
                "learning_rate": 0.001
            }
        }

# ============================================================================
# Model Cache and Utilities
# ============================================================================

# Global model cache for lazy loading
model_cache = {}

def normalize_features(features: np.ndarray) -> np.ndarray:
    """
    Normalize features using fitted scaler.
    
    Args:
        features: Input feature vector or matrix
    
    Returns:
        Normalized features
    """
    # Load scaler if not in cache
    if 'scaler' not in model_cache:
        scaler_path = Path('data/scalers/feature_scaler.pkl')
        if scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                model_cache['scaler'] = pickle.load(f)
        else:
            logger.warning("Scaler not found, returning features as-is")
            return features
    
    scaler = model_cache['scaler']
    return scaler.transform(features.reshape(1, -1)) if features.ndim == 1 else scaler.transform(features)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])
