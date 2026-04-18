"""
FastAPI application for AIPMS (AI-Powered Predictive Maintenance System).

Phase 4: Backend API for ML Model Inference

Provides REST endpoints for:
- Single & batch predictions (anomaly, failure, RUL)
- Ensemble predictions (all 3 models combined)
- Model management and status
- Health checks and metrics

The API serves as the interface between the trained ML models (Phase 3) 
and external applications (dashboard, monitoring systems).

Architecture:
- Predictions are routed to dedicated modules with model caching
- All models loaded once at first use (lazy initialization)
- Responses standardized with timing/status information
- Error handling with meaningful messages
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AIPMS API",
    description="AI-Powered Predictive Maintenance System REST API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global models cache for lazy loading
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

class DataLoadRequest(BaseModel):
    dataset: str = "FD001"
    use_synthetic: bool = True

class FeatureEngineerRequest(BaseModel):
    pass

class AnomalyDetectorTrainRequest(BaseModel):
    n_estimators: int = 200
    contamination: float = 0.05
    random_state: int = 42

class FailurePredictorTrainRequest(BaseModel):
    max_depth: int = 10
    learning_rate: float = 0.1
    random_state: int = 42

class RULEstimatorTrainRequest(BaseModel):
    sequence_length: int = 5
    lstm_units: int = 64
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 10

class PredictionRequest(BaseModel):
    X: List[List[float]]

class MetricsRequest(BaseModel):
    X: List[List[float]]
    y: List[float]

# ============================================================================
# Global State
# ============================================================================

cache = {
    "X_raw": None,
    "y_raw": None,
    "X_engineered": None,
    "y_engineered": None,
    "anomaly_detector": None,
    "failure_predictor": None,
    "rul_estimator": None,
    "scaler": None,
}


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", tags=["health"])
async def root():
    """Root endpoint - service status."""
    return {
        "service": "AIPMS API",
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# ============================================================================
# Data Loading Endpoints
# ============================================================================

@app.post("/data/load", tags=["data"])
async def load_data(request: DataLoadRequest):
    """Load dataset."""
    try:
        from models.train.data_manager import DatasetManager
        
        dm = DatasetManager()
        X, y = dm.load(request.dataset, use_synthetic=request.use_synthetic)
        
        # Store in cache
        cache["X_raw"] = X.astype(np.float32)
        cache["y_raw"] = y.astype(np.float32)
        
        return {
            "status": "loaded",
            "dataset": request.dataset,
            "n_samples": len(X),
            "n_features": X.shape[1]
        }
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Feature Engineering Endpoints
# ============================================================================

@app.post("/features/engineer", tags=["features"])
async def engineer_features(request: FeatureEngineerRequest):
    """Engineer features from raw data."""
    try:
        if cache["X_raw"] is None:
            raise ValueError("No raw data loaded. Call /data/load first.")
        
        from models.train.feature_engineer import FeatureEngineer
        
        # Engineer features (normalize + rolling features)
        fe = FeatureEngineer(window_size=5)
        X_normalized = fe.normalize(cache["X_raw"])
        X_engineered = fe.compute_rolling_features(X_normalized)
        
        # Store in cache
        cache["X_engineered"] = X_engineered.astype(np.float32)
        cache["scaler"] = fe
        
        return {
            "status": "engineered",
            "n_samples": len(X_engineered),
            "n_features": X_engineered.shape[1]
        }
    except Exception as e:
        logger.error(f"Error engineering features: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================

@app.post("/anomaly/train", tags=["anomaly"])
async def train_anomaly_detector(request: AnomalyDetectorTrainRequest):
    """Train anomaly detection model."""
    try:
        if cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        
        from models.train.anomaly_detector import AnomalyDetector
        
        detector = AnomalyDetector(
            n_estimators=request.n_estimators,
            contamination=request.contamination,
            random_state=request.random_state
        )
        detector.fit(cache["X_engineered"])
        cache["anomaly_detector"] = detector
        
        return {
            "status": "trained",
            "model": "AnomalyDetector",
            "n_estimators": request.n_estimators,
            "contamination": request.contamination
        }
    except Exception as e:
        logger.error(f"Error training anomaly detector: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/anomaly/predict", tags=["anomaly"])
async def predict_anomaly(request: PredictionRequest):
    """Predict anomalies."""
    try:
        if cache["anomaly_detector"] is None:
            raise ValueError("Anomaly detector not trained. Call /anomaly/train first.")
        
        X = np.array(request.X, dtype=np.float32)
        scores = cache["anomaly_detector"].score_samples(X)
        predictions = cache["anomaly_detector"].predict(X)
        
        return {
            "scores": scores.tolist(),
            "predictions": predictions.tolist(),
            "n_samples": len(scores)
        }
    except Exception as e:
        logger.error(f"Error predicting anomalies: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Failure Prediction Endpoints
# ============================================================================

@app.post("/failure/train", tags=["failure"])
async def train_failure_predictor(request: FailurePredictorTrainRequest):
    """Train failure prediction model."""
    try:
        if cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        if cache["y_raw"] is None:
            raise ValueError("No labels. Call /data/load first.")
        
        from models.train.failure_predictor import FailurePredictor
        
        # Create binary labels (failure in next 7 days)
        y_binary = (cache["y_raw"] <= 7).astype(int)
        
        predictor = FailurePredictor(
            max_depth=request.max_depth,
            learning_rate=request.learning_rate,
            random_state=request.random_state
        )
        predictor.fit(cache["X_engineered"], y_binary)
        cache["failure_predictor"] = predictor
        
        return {
            "status": "trained",
            "model": "FailurePredictor",
            "max_depth": request.max_depth,
            "learning_rate": request.learning_rate
        }
    except Exception as e:
        logger.error(f"Error training failure predictor: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/failure/predict", tags=["failure"])
async def predict_failure(request: PredictionRequest):
    """Predict failures."""
    try:
        if cache["failure_predictor"] is None:
            raise ValueError("Failure predictor not trained. Call /failure/train first.")
        
        X = np.array(request.X, dtype=np.float32)
        predictions = cache["failure_predictor"].predict(X)
        probabilities = cache["failure_predictor"].predict_proba(X)
        
        return {
            "predictions": predictions.tolist(),
            "probabilities": probabilities[:, 1].tolist(),
            "n_samples": len(predictions)
        }
    except Exception as e:
        logger.error(f"Error predicting failures: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# RUL Estimation Endpoints
# ============================================================================

@app.post("/rul/train", tags=["rul"])
async def train_rul_estimator(request: RULEstimatorTrainRequest):
    """Train RUL estimation model."""
    try:
        if cache["X_engineered"] is None:
            raise ValueError("No engineered features. Call /features/engineer first.")
        if cache["y_raw"] is None:
            raise ValueError("No labels. Call /data/load first.")
        
        from models.train.rul_estimator import RULEstimator
        
        estimator = RULEstimator(
            sequence_length=request.sequence_length,
            lstm_units=request.lstm_units,
            dropout_rate=request.dropout_rate,
            learning_rate=request.learning_rate,
            epochs=request.epochs
        )
        estimator.fit(
            cache["X_engineered"],
            cache["y_raw"],
            validation_split=0.2,
            verbose=0
        )
        cache["rul_estimator"] = estimator
        
        return {
            "status": "trained",
            "model": "RULEstimator",
            "sequence_length": request.sequence_length,
            "lstm_units": request.lstm_units,
            "epochs": request.epochs
        }
    except Exception as e:
        logger.error(f"Error training RUL estimator: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rul/predict", tags=["rul"])
async def predict_rul(request: PredictionRequest):
    """Predict RUL."""
    try:
        if cache["rul_estimator"] is None:
            raise ValueError("RUL estimator not trained. Call /rul/train first.")
        
        X = np.array(request.X, dtype=np.float32)
        predictions = cache["rul_estimator"].predict(X)
        
        return {
            "predictions": predictions.tolist(),
            "n_samples": len(predictions)
        }
    except Exception as e:
        logger.error(f"Error predicting RUL: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Model Status Endpoint
# ============================================================================

@app.get("/status", tags=["status"])
async def get_status():
    """Get model training status."""
    return {
        "data_loaded": cache["X_raw"] is not None,
        "features_engineered": cache["X_engineered"] is not None,
        "anomaly_detector_trained": cache["anomaly_detector"] is not None,
        "failure_predictor_trained": cache["failure_predictor"] is not None,
        "rul_estimator_trained": cache["rul_estimator"] is not None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("AIPMS API starting up...")
    logger.info("Phase 4: Backend API for ML Model Inference")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("AIPMS API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
