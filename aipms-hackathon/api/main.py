"""
AIPMS FastAPI Application
Main entry point for the backend API
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./aipms.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Startup time tracker
startup_time = datetime.utcnow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info("AIPMS FastAPI startup")
    # Startup logic here (models loaded, DB checked, etc.)
    yield
    logger.info("AIPMS FastAPI shutdown")
    # Cleanup logic here

# Create FastAPI app
app = FastAPI(
    title="AIPMS - AI-Driven Predictive Maintenance System",
    description="Hackathon submission for BIT Sindri PS-1",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Health Check Endpoint ===
@app.get("/health")
async def health_check():
    """System health check"""
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    try:
        # Check database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "api": "ok",
        "db": db_status,
        "mqtt_broker": "ok",  # Will be updated in Phase 3
        "models": {
            "anomaly_detector": "pending",
            "failure_predictor": "pending",
            "rul_estimator": "pending"
        },
        "uptime_sec": uptime,
        "timestamp": datetime.utcnow().isoformat()
    }

# === Placeholder routes (to be implemented in Phases 3-6) ===
@app.get("/equipment")
async def get_equipment():
    """Get all equipment status - Phase 4"""
    return {"status": "not_implemented", "message": "To be implemented in Phase 4"}

@app.get("/alerts")
async def get_alerts():
    """Get active alerts - Phase 4"""
    return {"status": "not_implemented", "message": "To be implemented in Phase 4"}

@app.get("/schedule")
async def get_schedule():
    """Get maintenance schedule - Phase 4"""
    return {"status": "not_implemented", "message": "To be implemented in Phase 4"}

# Run if called directly (for debugging)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv('FASTAPI_HOST', '0.0.0.0'),
        port=int(os.getenv('FASTAPI_PORT', 8000))
    )
