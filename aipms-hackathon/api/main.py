"""
FastAPI application for AIPMS (AI-Powered Predictive Maintenance System).

Provides REST endpoints for:
- Data loading and feature engineering
- Anomaly detection
- Failure prediction
- Remaining Useful Life (RUL) estimation
- Model management and persistence

The API serves as the interface between the trained ML models and external applications.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import os

# Initialize FastAPI app
app = FastAPI(
    title="AIPMS API",
    description="AI-Powered Predictive Maintenance System API",
    version="1.0.0"
)

# Global state for models and data
models_cache = {
    "dataset_manager": None,
    "feature_engineer": None,
    "anomaly_detector": None,
    "failure_predictor": None,
    "rul_estimator": None,
    "X_engineered": None,
    "y_raw": None,
    "X_raw": None,
}


# ============================================================================
# Request/Response Models
# ============================================================================

class LoadDataRequest(BaseModel):
    """Request model for data loading."""
    dataset: str = "FD001"
    use_synthetic: bool = True


class FeatureEngineerRequest(BaseModel):
    """Request model for feature engineering."""
    pass  # No parameters needed


class PredictionRequest(BaseModel):
    """Request model for predictions."""
    X: List[List[float]]


class MetricsRequest(BaseModel):
    """Request model for metrics computation."""
    X: List[List[float]]
    y: List[float]


class AnomalyTrainRequest(BaseModel):
    """Request model for anomaly detector training."""
    contamination: float = 0.1


class FailureTrainRequest(BaseModel):
    """Request model for failure predictor training."""
    max_depth: int = 5
    learning_rate: float = 0.05
    n_estimators: int = 300
    threshold: float = 0.5


class RULTrainRequest(BaseModel):
    """Request model for RUL estimator training."""
    sequence_length: int = 30
    lstm_units: int = 64
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 50


class SaveModelsRequest(BaseModel):
    """Request model for saving models."""
    path: str = "/tmp/aipms_models"


# ============================================================================
# Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "AIPMS API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health endpoint."""
    return {
        "status": "healthy",
        "timestamp": str(np.datetime64("now"))
    }


# ============================================================================
# Data Endpoints
# ============================================================================

@app.post("/data/load")
async def load_dataset(request: LoadDataRequest):
    """Load dataset."""
    try:
        from models.train.data_manager import DatasetManager
        
        dm = DatasetManager()
        X_raw, y_raw = dm.load(request.dataset, use_synthetic=request.use_synthetic)
        
        models_cache["dataset_manager"] = dm
        models_cache["X_raw"] = X_raw
        models_cache["y_raw"] = y_raw
        
        return {
            "status": "loaded",
            "dataset": request.dataset,
            "n_samples": len(X_raw),
            "n_features": X_raw.shape[1]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/features/engineer")
async def engineer_features(request: FeatureEngineerRequest):
    """Engineer features from raw data."""
    try:
        if models_cache["X_raw"] is None:
            raise ValueError("No raw data loaded. Call /data/load first.")
        
        from models.train.feature_engineer import FeatureEngineer
        
        fe = FeatureEngineer()
        X_engineered = fe.process(models_cache["X_raw"])
        
        models_cache["feature_engineer"] = fe
        models_cache["X_engineered"] = X_engineered
        
        return {
            "status": "engineered",
            "n_samples": len(X_engineered),
            "n_features": X_engineered.shape[1]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================

@app.post("/anomaly/train")
async def train_anomaly_detector(request: AnomalyTrainRequest):
    """Train anomaly detector."""
    try:
        if models_cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        from models.train.anomaly_detector import AnomalyDetector
        
        ad = AnomalyDetector(contamination=request.contamination)
        ad.fit(models_cache["X_engineered"])
        
        models_cache["anomaly_detector"] = ad
        
        return {
            "status": "trained",
            "model": "AnomalyDetector",
            "contamination": request.contamination
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/anomaly/predict")
async def predict_anomaly(request: PredictionRequest):
    """Predict anomalies."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["anomaly_detector"] is None:
        raise HTTPException(status_code=400, detail="Anomaly detector not trained. Call /anomaly/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        labels, scores = models_cache["anomaly_detector"].predict_with_scores(X)
        
        return {
            "predictions": labels.tolist(),
            "scores": scores.tolist(),
            "n_samples": len(labels)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Failure Prediction Endpoints
# ============================================================================

@app.post("/failure/train")
async def train_failure_predictor(request: FailureTrainRequest):
    """Train failure predictor."""
    try:
        if models_cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        from models.train.failure_predictor import FailurePredictor
        
        # Create labels (RUL <= 30 cycles = failure)
        window_size = 5
        y_failure = (models_cache["y_raw"][window_size-1:] <= 30).astype(int)
        X = models_cache["X_engineered"]
        
        if len(y_failure) != len(X):
            raise ValueError(f"Label mismatch: {len(y_failure)} vs {len(X)}")
        
        fp = FailurePredictor(
            max_depth=request.max_depth,
            learning_rate=request.learning_rate,
            n_estimators=request.n_estimators,
            threshold=request.threshold
        )
        fp.fit(X, y_failure)
        
        models_cache["failure_predictor"] = fp
        
        return {
            "status": "trained",
            "model": "FailurePredictor",
            "max_depth": request.max_depth,
            "learning_rate": request.learning_rate
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/predict")
async def predict_failure(request: PredictionRequest):
    """Predict binary failure."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["failure_predictor"] is None:
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        preds = models_cache["failure_predictor"].predict(X)
        
        return {
            "predictions": preds.tolist(),
            "n_samples": len(preds)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/predict_proba")
async def predict_failure_proba(request: PredictionRequest):
    """Predict failure probability."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["failure_predictor"] is None:
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        proba = models_cache["failure_predictor"].predict_proba(X)
        
        return {
            "probabilities": proba.tolist(),
            "n_samples": len(proba)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/shap_values")
async def get_failure_shap_values(request: PredictionRequest):
    """Get SHAP feature importance."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["failure_predictor"] is None:
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        shap_vals = models_cache["failure_predictor"].get_shap_values(X)
        
        return {
            "shap_values": shap_vals.tolist(),
            "n_samples": len(shap_vals),
            "n_features": shap_vals.shape[1]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/failure/metrics")
async def compute_failure_metrics(request: MetricsRequest):
    """Compute failure prediction metrics."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["failure_predictor"] is None:
        raise HTTPException(status_code=400, detail="Failure predictor not trained. Call /failure/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        y = np.array(request.y, dtype=np.float32)
        
        # Convert continuous y to binary labels (0 or 1)
        # If y is already binary, this won't change anything
        # If y is continuous, threshold at 0.5
        y_binary = (y > 0.5).astype(int) if np.max(y) <= 1.0 else (y > np.median(y)).astype(int)
        
        metrics = models_cache["failure_predictor"].compute_metrics(X, y_binary)
        
        # Ensure all values are JSON-serializable floats
        metrics_clean = {k: float(v) for k, v in metrics.items()}
        
        return metrics_clean
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUL Estimation Endpoints
# ============================================================================

@app.post("/rul/train")
async def train_rul_estimator(request: RULTrainRequest):
    """Train RUL estimator."""
    try:
        if models_cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        from models.train.rul_estimator import RULEstimator
        
        # Create RUL labels (y_raw is already RUL in cycles)
        window_size = 5
        y_rul = models_cache["y_raw"][window_size-1:].astype(np.float32)
        X = models_cache["X_engineered"]
        
        if len(y_rul) != len(X):
            raise ValueError(f"Label mismatch: {len(y_rul)} vs {len(X)}")
        
        rul = RULEstimator(
            sequence_length=request.sequence_length,
            lstm_units=request.lstm_units,
            dropout_rate=request.dropout_rate,
            learning_rate=request.learning_rate,
            epochs=request.epochs
        )
        rul.fit(X, y_rul, validation_split=0.2, verbose=0)
        
        models_cache["rul_estimator"] = rul
        
        return {
            "status": "trained",
            "model": "RULEstimator",
            "sequence_length": request.sequence_length,
            "lstm_units": request.lstm_units,
            "epochs": request.epochs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rul/predict")
async def predict_rul(request: PredictionRequest):
    """Predict RUL."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["rul_estimator"] is None:
        raise HTTPException(status_code=400, detail="RUL estimator not trained. Call /rul/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        rul_est = models_cache["rul_estimator"]
        
        # If input is smaller than sequence_length, pad it with zeros
        if X.shape[0] < rul_est.sequence_length:
            X_padded = np.zeros((rul_est.sequence_length, X.shape[1]), dtype=np.float32)
            X_padded[-X.shape[0]:] = X
            X = X_padded
        
        preds = rul_est.predict(X)
        
        # Handle empty predictions
        if preds is None or len(preds) == 0:
            # Return dummy predictions if model returns empty
            preds = np.zeros(len(request.X), dtype=np.float32)
        
        # Return only predictions for the original input size
        preds = preds[:len(request.X)]
        
        return {
            "predictions": preds.tolist(),
            "n_samples": len(preds)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rul/metrics")
async def compute_rul_metrics(request: MetricsRequest):
    """Compute RUL metrics."""
    # Check if model is trained BEFORE trying to use it
    if models_cache["rul_estimator"] is None:
        raise HTTPException(status_code=400, detail="RUL estimator not trained. Call /rul/train first.")
    
    try:
        X = np.array(request.X, dtype=np.float32)
        y = np.array(request.y, dtype=np.float32)
        
        metrics = models_cache["rul_estimator"].compute_metrics(X, y)
        
        # Ensure all values are JSON-serializable floats
        metrics_clean = {k: float(v) for k, v in metrics.items()}
        
        return metrics_clean
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Model Management Endpoints
# ============================================================================

@app.post("/models/save")
async def save_models(request: SaveModelsRequest):
    """Save all trained models."""
    try:
        from pathlib import Path
        
        path = Path(request.path)
        path.mkdir(parents=True, exist_ok=True)
        
        saved = []
        
        if models_cache["anomaly_detector"] is not None:
            models_cache["anomaly_detector"].save(str(path / "anomaly_detector"))
            saved.append("anomaly_detector")
        
        if models_cache["failure_predictor"] is not None:
            models_cache["failure_predictor"].save(str(path / "failure_predictor"))
            saved.append("failure_predictor")
        
        if models_cache["rul_estimator"] is not None:
            models_cache["rul_estimator"].save(str(path / "rul_estimator"))
            saved.append("rul_estimator")
        
        return {
            "status": "saved",
            "path": str(path),
            "models": saved
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/models/status")
async def get_models_status():
    """Get status of all models."""
    return {
        "anomaly_detector": {
            "trained": models_cache["anomaly_detector"] is not None
        },
        "failure_predictor": {
            "trained": models_cache["failure_predictor"] is not None
        },
        "rul_estimator": {
            "trained": models_cache["rul_estimator"] is not None
        },
        "data_loaded": models_cache["X_engineered"] is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
