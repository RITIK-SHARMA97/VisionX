# AIPMS Hackathon - Setup & Scaffolding Complete ✅

## Project Overview

**AI-Driven Predictive Maintenance System (AIPMS)**  
BIT Sindri Hackathon 2025 | Problem Statement PS-1: AI & Data Analytics

This is the **Phase 1: Setup & Scaffolding** deliverable for the 36-hour hackathon. All project structure, dependencies, database schema, and scaffold code are ready for Phase 2-7 implementation.

---

## 📋 Phase 1 Deliverables

### ✅ Project Structure (13 directories)
- `data/` - C-MAPSS dataset and processed features
- `models/` - Training scripts and saved model weights
- `simulator/` - Equipment sensor simulator + MQTT publisher
- `api/` - FastAPI backend (models, routes, main app)
- `dashboard/` - Streamlit multi-page dashboard
- `tests/` - Unit and integration test suite
- `config/` - Database schema, MQTT config, env templates
- `logs/` - Runtime logs directory

### ✅ Configuration Files
- `.env` - Local environment variables (13 settings)
- `.env.example` - Template for team setup
- `.gitignore` - Ignores sensitive files and artifacts
- `config/mosquitto.conf` - MQTT broker configuration
- `config/schema.sql` - SQLite schema with 5 tables + 3 indexes

### ✅ Dependencies (18 packages)
```
requirements.txt pinned versions:
- pandas==2.2.0, numpy==1.24.3
- scikit-learn==1.3.2, xgboost==2.0.3, torch==2.1.1
- streamlit==1.32.0, plotly==5.18.0
- fastapi==0.110.0, uvicorn==0.29.0
- paho-mqtt==1.6.1, sqlalchemy==2.0.23
- APScheduler==3.10.4, pytest==8.0.0
```

### ✅ Python Scaffolding
- `api/models/orm.py` - SQLAlchemy table definitions (6 models)
- `api/models/schema.py` - Pydantic request/response schemas
- `api/main.py` - FastAPI app with /health endpoint + lifespan
- `simulator/simulator.py` - Equipment lifecycle simulator (1 Hz MQTT publish)
- `simulator/mqtt_subscriber.py` - MQTT consumer + data processor
- `dashboard/app.py` - Streamlit page with navigation skeleton
- `models/train/preprocess.py` - ML preprocessing stubs

### ✅ Startup Scripts
- `start.ps1` - Windows PowerShell automation (6-step initialization)
- `start.sh` - Linux/macOS bash automation (6-step initialization)
- Both scripts: Install deps, init DB, verify imports, test connectivity

### ✅ Test Suite
- `tests/test_setup.py` - 8 verification tests
  - Project structure validation
  - Requirements.txt completeness
  - Database schema and equipment units
  - Python imports
  - Configuration files

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.10+
- sqlite3 (typically included)
- Optional: Docker (for MQTT broker)

### Option 1: Automated Setup (Recommended)

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Linux/macOS (Bash):**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   sqlite3 aipms.db < config/schema.sql
   ```

3. **Verify setup:**
   ```bash
   pytest tests/test_setup.py -v
   ```

---

## 🏗️ Architecture

### 5-Layer IoT + AI System

```
Layer 1 (Physical)     → Equipment sensors (simulated at 1 Hz)
     ↓
Layer 2 (IoT Edge)     → MQTT publisher (paho-mqtt) → Mosquitto broker
     ↓
Layer 3 (Ingestion)    → MQTT subscriber → SQLite database
     ↓
Layer 4 (Processing)   → FastAPI inference service → ML models
     ↓
Layer 5 (Presentation) → Streamlit dashboard (live updates, alerts)
```

### Technology Stack

| Component | Technology | Role |
|-----------|-----------|------|
| IoT Protocol | MQTT (Mosquitto) | Real-time sensor streaming |
| ML Models | Isolation Forest, XGBoost, LSTM | Anomaly, failure, RUL prediction |
| Backend | FastAPI + SQLAlchemy | API + ORM for data persistence |
| Frontend | Streamlit + Plotly | Engineer dashboard + visualizations |
| Database | SQLite | Local development storage |
| Scheduler | APScheduler | Periodic model inference (10-sec windows) |

---

## 📊 Database Schema

### 5 Core Tables
- **equipment** - Mining equipment units (EXC-01, DMP-03, CVR-01)
- **sensor_readings** - Raw telemetry from MQTT (temperature, vibration, pressure, RPM)
- **predictions** - ML model outputs (anomaly score, failure probability, RUL)
- **alerts** - Actionable notifications with SHAP attribution
- **maintenance_jobs** - Prioritized maintenance schedule

### Initial Data
```sql
3 Equipment Units pre-loaded:
- EXC-01: Rope Shovel (excavator) | North Bench
- DMP-03: Dumper Truck (dumper) | Main Haul Road
- CVR-01: Belt Conveyor (conveyor) | Ore Processing
```

---

## 🧪 Verification

### Run Test Suite
```bash
pytest tests/test_setup.py -v
```

**Expected Output (8/8 PASSED):**
```
test_project_structure_exists     PASSED ✅
test_requirements_file_exists     PASSED ✅
test_env_file_exists              PASSED ✅
test_database_schema_exists       PASSED ✅
test_python_imports               PASSED ✅
test_mosquitto_config_exists      PASSED ✅
test_startup_scripts_exist        PASSED ✅
test_gitignore_exists             PASSED ✅
```

### Manual Verification
```bash
# Check database
sqlite3 aipms.db ".tables"           # Should show 5 tables
sqlite3 aipms.db "SELECT COUNT(*) FROM equipment;"  # Should show 3

# Test Python imports
python -c "from api.models.orm import Equipment; print('✅ ORM imported')"

# Check MQTT connectivity (when broker running)
mosquitto_sub -t "test" &
```

---

## 📈 Phase Timeline

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| **Phase 1** | 2 hours | Setup & Scaffolding | ✅ COMPLETE |
| **Phase 2A** | 3 hours | IoT Pipeline (MQTT, Simulator, Subscriber) | ⏳ Next |
| **Phase 2B** | 3 hours | ML Data Prep (Preprocessing, Features, Labels) | ⏳ Next |
| **Phase 3** | 8 hours | Model Training (Anomaly, Failure, RUL) | Pending |
| **Phase 4** | 5 hours | FastAPI Backend (Routes, Inference, Scheduling) | Pending |
| **Phase 5** | 6 hours | Streamlit Dashboard (5 screens, Real-time Updates) | Pending |
| **Phase 6** | 3 hours | Integration (MQTT ↔ API ↔ Dashboard) | Pending |
| **Phase 7** | 2 hours | Polish & Documentation | Pending |
| **Buffer** | 7 hours | Contingencies & Testing | Pending |
| **Total** | 36 hours | Working Hackathon Submission | In Progress |

---

## 🔧 Environment Configuration

### .env Variables (13 settings)

```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_QOS=1
MQTT_TIMEOUT=60

# Database
DATABASE_URL=sqlite:///./aipms.db
SQLITE_DB_PATH=./aipms.db

# Models
MODEL_DIR=./models/saved
MODEL_VERSION=1.0.0

# Simulator
SIMULATOR_UNITS=3
SIMULATOR_HZ=1
SIMULATOR_SPEED_MULTIPLIER=1.0

# API
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
LOG_LEVEL=INFO

# Dashboard
STREAMLIT_PORT=8501

# Inference
INFERENCE_BATCH_SIZE=32
INFERENCE_TIMEOUT_MS=100

# Features
FEATURE_WINDOW_SIZE=5
RUL_CONFIDENCE_PERCENTILE=95

# Debug
DEBUG=false
```

---

## 📚 File Manifest

### Configuration & Setup
- ✅ requirements.txt (18 packages)
- ✅ .env (local config)
- ✅ .env.example (template)
- ✅ .gitignore (security)
- ✅ config/schema.sql (DB schema)
- ✅ config/mosquitto.conf (MQTT config)
- ✅ start.ps1 (Windows automation)
- ✅ start.sh (Unix automation)

### Python Modules
- ✅ api/main.py (FastAPI skeleton)
- ✅ api/models/orm.py (SQLAlchemy models)
- ✅ api/models/schema.py (Pydantic schemas)
- ✅ simulator/simulator.py (Equipment simulator)
- ✅ simulator/mqtt_subscriber.py (MQTT consumer)
- ✅ dashboard/app.py (Streamlit skeleton)
- ✅ models/train/preprocess.py (ML stubs)

### Testing
- ✅ tests/test_setup.py (8 verification tests)

### Package Markers
- ✅ 9 × __init__.py files (Python package markers)

---

## 🎯 Success Criteria (Phase 1)

- [x] All 13 directories created
- [x] All configuration files generated
- [x] SQLite schema with 5 tables + 3 indexes
- [x] 18 dependencies documented in requirements.txt
- [x] Python ORM, schema, API, simulator, dashboard scaffolds complete
- [x] Startup scripts (Windows + Unix) functional
- [x] Test suite: 8/8 passing
- [x] .gitignore prevents secret leakage
- [x] README with quick-start instructions

---

## ⚡ What's Next (Phase 2A & 2B)

### Phase 2A: IoT Pipeline (3 hours)
1. Implement full SensorSimulator with lifecycle curves
2. Enhance MQTTSubscriber with data quality checks + DB writes
3. Verify 1 Hz data flow into SQLite
4. Set up MQTT broker connectivity

### Phase 2B: ML Data Prep (3 hours)
1. Download NASA C-MAPSS dataset
2. Implement preprocessing pipeline (normalization, windowing, feature engineering)
3. Create RUL labels and train/val split
4. Generate scaler .pkl files for inference

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `sqlite3 not found` | Install: `apt-get install sqlite3` (Linux) or use Python sqlite3 module |
| `pip install` fails | Try: `pip install --upgrade pip` then retry |
| MQTT connection refused | Ensure mosquitto running: `mosquitto -c config/mosquitto.conf` |
| Port already in use | Check: `lsof -i :1883` (MQTT), `:8000` (API), `:8501` (Streamlit) |
| Python import errors | Verify venv activated: `source venv/bin/activate` (Unix) or `.\.venv\Scripts\Activate.ps1` (Windows) |

---

## 📞 Team Contact

**Hackathon Team**: AIPMS  
**Mentor**: Prof. Prakash Kumar (Dept. of Production & Industrial Engineering)  
**Institution**: BIT Sindri, Dhanbad, Jharkhand  
**Timeline**: April 2025 (36 hours)

---

## 📄 License & Attribution

**Project**: AI-Driven Predictive Maintenance System (AIPMS)  
**Problem Statement**: PS-1 (AI & Data Analytics)  
**Event**: BIT Sindri Hackathon 2025  
**Status**: ✅ Phase 1 Complete | Phase 2+ In Progress

---

**Phase 1 Completed**: April 17, 2026  
**Delivery Status**: All Phase 1 artifacts delivered ✅  
**Next Phase**: Phase 2A & 2B (IoT + ML Preparation)
