"""
Batch Prediction Routes

Handles batch processing of multiple samples through ML models.
Optimized for vectorized operations using NumPy.
"""

import logging
import time
from typing import List, Dict, Any
import numpy as np
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Import model cache from predictions module
# (In production, this should be a shared singleton)
from .predictions import model_cache, normalize_features

# ============================================================================
# Data Models
# ============================================================================

class BatchRequest(BaseModel):
    """Request model for batch predictions."""
    batch: List[List[float]] = Field(..., description="List of feature vectors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch": [
                    [0.45, 52.3, 1.2, 2100, 18.5, 0.052, 0.048, 0.051, 0.049, 0.050, 0.051],
                    [0.50, 55.1, 1.3, 2150, 19.2, 0.055, 0.050, 0.052, 0.051, 0.051, 0.052]
                ]
            }
        }


class BatchResponse(BaseModel):
    """Response model for batch predictions."""
    status: str
    data: Dict[str, Any]
    timestamp: str
    latency_ms: float


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])


# ============================================================================
# Helper Functions
# ============================================================================

def validate_batch(batch: List[List[float]]) -> None:
    """
    Validate batch dimensions and values.
    
    Args:
        batch: List of feature vectors
    
    Raises:
        HTTPException: If validation fails
    """
    if len(batch) == 0:
        raise HTTPException(status_code=400, detail="Batch cannot be empty")
    
    if len(batch) > 10000:
        raise HTTPException(status_code=400, detail="Batch size too large (max 10,000)")
    
    for i, sample in enumerate(batch):
        if len(sample) != 11:
            raise HTTPException(
                status_code=400,
                detail=f"Sample {i}: Expected 11 features, got {len(sample)}"
            )
        
        # Check for NaN or infinite values
        X = np.array(sample)
        if not np.all(np.isfinite(X)):
            raise HTTPException(
                status_code=400,
                detail=f"Sample {i}: Contains NaN or infinite values"
            )


def normalize_batch(batch: List[List[float]]) -> np.ndarray:
    """
    Normalize batch of features using fitted scaler.
    
    Args:
        batch: Batch of feature vectors
    
    Returns:
        Normalized batch array
    """
    try:
        X = np.array(batch, dtype=np.float32)
        
        if model_cache.scaler is None:
            logger.warning("Scaler not available, using raw features")
            return X
        
        X_normalized = model_cache.scaler.transform(X)
        return X_normalized
    
    except Exception as e:
        logger.error(f"Batch normalization failed: {e}")
        raise HTTPException(status_code=400, detail=f"Normalization error: {str(e)}")


# ============================================================================
# Batch Anomaly Detection
# ============================================================================

@router.post("/anomaly", response_model=BatchResponse)
async def batch_predict_anomaly(request: BatchRequest) -> BatchResponse:
    """
    Predict anomaly scores for a batch of samples.
    
    Vectorized operation: processes entire batch at once.
    """
    start_time = time.time()
    
    try:
        # Ensure models loaded
        model_cache.ensure_loaded()
        
        # Validate batch
        validate_batch(request.batch)
        
        # Normalize batch
        X_normalized = normalize_batch(request.batch)
        
        # Get anomaly model
        if "model" not in model_cache.anomaly_detector:
            raise HTTPException(status_code=500, detail="Anomaly detector not loaded")
        
        anomaly_model = model_cache.anomaly_detector["model"]
        
        # Batch predict
        anomaly_scores = anomaly_model.score_samples(X_normalized)
        
        # Calibrate to [0, 1]
        score_min = model_cache.anomaly_detector.get("score_min_", -100)
        score_max = model_cache.anomaly_detector.get("score_max_", 0)
        
        if score_max > score_min:
            calibrated_scores = (score_max - anomaly_scores) / (score_max - score_min)
            calibrated_scores = np.clip(calibrated_scores, 0, 1)
        else:
            calibrated_scores = np.full_like(anomaly_scores, 0.5)
        
        # Determine labels for batch
        threshold_warning = model_cache.anomaly_detector.get("threshold_warning", 0.40)
        threshold_critical = model_cache.anomaly_detector.get("threshold_critical", 0.70)
        
        labels = np.empty(len(calibrated_scores), dtype=object)
        labels[calibrated_scores < threshold_warning] = "normal"
        labels[(calibrated_scores >= threshold_warning) & (calibrated_scores < threshold_critical)] = "warning"
        labels[calibrated_scores >= threshold_critical] = "critical"
        
        # Format predictions
        predictions = [
            {
                "score": float(round(score, 4)),
                "label": str(label)
            }
            for score, label in zip(calibrated_scores, labels)
        ]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return BatchResponse(
            status="success",
            data={
                "predictions": predictions,
                "batch_size": len(request.batch),
                "processed": len(predictions)
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            latency_ms=round(latency_ms, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch anomaly prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


# ============================================================================
# Batch Failure Prediction
# ============================================================================

@router.post("/failure", response_model=BatchResponse)
async def batch_predict_failure(request: BatchRequest) -> BatchResponse:
    """
    Predict failure probabilities for a batch of samples.
    """
    start_time = time.time()
    
    try:
        # Ensure models loaded
        model_cache.ensure_loaded()
        
        # Validate batch
        validate_batch(request.batch)
        
        # Normalize batch
        X_normalized = normalize_batch(request.batch)
        
        # Get failure model
        if "model" not in model_cache.failure_predictor:
            raise HTTPException(status_code=500, detail="Failure predictor not loaded")
        
        failure_model = model_cache.failure_predictor["model"]
        
        # Batch predict
        failure_probs = failure_model.predict_proba(X_normalized)[:, 1]
        
        # Determine risk levels
        risk_levels = np.empty(len(failure_probs), dtype=object)
        risk_levels[failure_probs < 0.3] = "low"
        risk_levels[(failure_probs >= 0.3) & (failure_probs < 0.7)] = "medium"
        risk_levels[failure_probs >= 0.7] = "high"
        
        # Format predictions
        predictions = [
            {
                "probability": float(round(prob, 4)),
                "risk_level": str(risk)
            }
            for prob, risk in zip(failure_probs, risk_levels)
        ]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return BatchResponse(
            status="success",
            data={
                "predictions": predictions,
                "batch_size": len(request.batch),
                "processed": len(predictions)
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            latency_ms=round(latency_ms, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch failure prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


# ============================================================================
# Batch RUL Estimation
# ============================================================================

@router.post("/rul", response_model=BatchResponse)
async def batch_predict_rul(request: BatchRequest) -> BatchResponse:
    """
    Predict RUL for a batch of samples.
    """
    start_time = time.time()
    
    try:
        # Ensure models loaded
        model_cache.ensure_loaded()
        
        # Validate batch
        validate_batch(request.batch)
        
        # Normalize batch
        X_normalized = normalize_batch(request.batch)
        
        # Get RUL model
        if "model" not in model_cache.rul_estimator:
            raise HTTPException(status_code=500, detail="RUL estimator not loaded")
        
        rul_model = model_cache.rul_estimator["model"]
        
        # Batch predict
        rul_estimates = rul_model.predict(X_normalized)
        rul_estimates = np.clip(rul_estimates, 0, 400)
        
        # Format predictions
        predictions = [
            {
                "rul_hours": float(round(rul, 1)),
                "confidence": {
                    "low": max(0, float(round(rul - 50, 1))),
                    "high": float(round(rul + 50, 1))
                }
            }
            for rul in rul_estimates
        ]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return BatchResponse(
            status="success",
            data={
                "predictions": predictions,
                "batch_size": len(request.batch),
                "processed": len(predictions)
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            latency_ms=round(latency_ms, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch RUL prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")
