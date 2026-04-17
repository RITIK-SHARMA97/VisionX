# AI-Driven Predictive Maintenance System (AIPMS) - Complete System Design

## Document Control

| Field | Detail |
|-------|--------|
| Problem Statement | PS-1 (AI & Data Analytics) - BIT Sindri Hackathon 2025 |
| Organization | Dept. of Production & Industrial Engineering, BIT Sindri |
| Mentor | Prof. Prakash Kumar |
| Document Version | v3.0 — Final Hackathon Edition |
| Classification | Hackathon Submission — Confidential |
| Prepared By | Team AIPMS |
| Date | April 2025 |
| Status | FINAL — Ready for Submission |

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | April 10, 2025 | Team AIPMS | Initial draft — Executive summary, problem statement, high-level architecture |
| v2.0 | April 12, 2025 | Team AIPMS | Added FMEA, cost model, user personas, requirements, ML design, API spec, security, deployment, testing |
| v3.0 | April 15, 2025 | Team AIPMS | Complete document — ToC, data dictionary, model comparison, alternative architectures, KPI design, cost optimization math, data quality, model drift, alert escalation, CMMS integration, IoT BOM, network topology, model governance, regulatory compliance, API JSON samples, references |

### Reading Guide

| Audience | Sections to Read |
|----------|-----------------|
| Judges evaluating PS-1 fulfilment | 1, 2, 5, 7, 9, 10 |
| Judges evaluating technical depth | 6, 7, 8, 11, 12 |
| Judges evaluating domain knowledge | 2, 3, 10, 16 |
| Judges evaluating innovation | 7.1, 7.2, 11, 15, 17 |
| Quick demo understanding | Section 14.3 (13-step demo script) |

---

## 1. Executive Summary

AIPMS is a full-stack, AI-powered software solution that transforms raw sensor telemetry from mining machinery into actionable maintenance intelligence. Targeted at open-cast coal mining operations in the Dhanbad region — home to Bharat Coking Coal Limited and Central Coalfields Limited — AIPMS directly addresses PS-1 by shifting the maintenance paradigm from reactive and scheduled approaches to a data-driven, condition-based predictive model.

AIPMS ingests real-time sensor streams (temperature, vibration, RPM, hydraulic pressure, electrical current, fuel consumption) through a five-layer IoT architecture, processes them through three independent ML models, and delivers equipment health insights, failure probability scores, Remaining Useful Life (RUL) estimates, and an AI-optimized maintenance schedule through a live web dashboard.

### PS-1 Requirements Coverage — at a Glance

| Requirement | Coverage |
|-------------|---------|
| DATA INTEGRATION | Real-time sensor ingestion via MQTT IoT pipeline + Python simulator |
| ANALYTICS | Anomaly detection (Isolation Forest) + Failure prediction (XGBoost) |
| LIFE ESTIMATION | RUL estimation via LSTM regression with asymmetric loss function |
| INTERFACE | 5-screen Streamlit dashboard with live charts, alerts, Gantt schedule |
| OPTIMIZATION | Priority-score optimizer + cost-minimization scheduling |
| ARCHITECTURE | 5-layer IoT + AI system design, network topology, component diagrams |

### Quantified Business Case

- **Annual savings per 10 machines**: Rs 6.5 Crore (Reactive: Rs 1.2 Cr/machine vs Predictive: Rs 0.55 Cr/machine)
- **Downtime reduction target**: 35-45% fewer unplanned stoppage hours
- **False positive alert budget**: < 5% (engineers cannot afford alert fatigue)
- **Failure prediction horizon**: 7 days advance warning — sufficient for planned maintenance
- **Regulatory alignment**: DGMS Circular No. 3 of 2012 on machinery inspection compliance

---

## 2. Problem Statement & Domain Analysis

### 2.1 Industry Context

Open-cast coal mining in Jharkhand's Dhanbad-Bokaro belt operates under intense production pressure: mines run three 8-hour shifts continuously, with equipment operating 16–22 hours per day. A rope shovel (excavator) represents a capital investment of Rs 15–25 Crore. When one fails unexpectedly, the cascading effect halts an entire production bench, disrupts railway loading schedules, and triggers penalties under Coal India dispatch contracts.

The Directorate General of Mines Safety (DGMS) mandates periodic equipment inspection under the Coal Mines Regulations 2017 and various DGMS circulars. However, mandatory inspections are schedule-based and do not account for condition-based degradation — creating a compliance gap that AIPMS closes by generating condition reports tied to real sensor data.

### 2.2 Maintenance Strategy Comparison

| Strategy | Trigger | Typical Cost per Machine/Year | Unplanned Downtime | Regulatory Status |
|----------|---------|-------------------------------|-------------------|-------------------|
| Reactive (Breakdown) | Equipment fails | Rs 1.2 Crore+ | 3–7 days/month | Fails DGMS Reg 100(2) inspection requirements |
| Preventive (Scheduled) | Fixed time interval (e.g., every 500 hrs) | Rs 80 Lakh | 1–2 days/month | Compliant but inefficient |
| Predictive (AIPMS) | Sensor condition + ML prediction | Rs 55 Lakh | < 4 hrs/month | Exceeds compliance — audit trail generated |

### 2.3 Equipment Taxonomy

| Equipment Class | Fleet Size | Capital Value | Key Subsystems | MTBF | Criticality |
|-----------------|------------|---------------|----------------|------|-------------|
| Rope Shovel/Excavator | 2-4 units | Rs 15-25 Cr | Swing gearbox, crowd system, hoist, hydraulics | 800-1200 hrs | Critical - bottleneck machine |
| Rear Dump Truck (35T-100T) | 8-15 units | Rs 3-8 Cr | Engine, transmission, suspension struts, tyres | 600-900 hrs | High - fleet redundancy available |
| Belt Conveyor | 3-8 systems | Rs 2-12 Cr | Drive motors, idler rollers, belt, takeup | 1500-2500 hrs | Critical - no alternative ore path |
| Drill (rotary/DTH) | 2-3 units | Rs 2-5 Cr | Rotary head, compressor, mast | 400-700 hrs | Medium |

### 2.4 Failure Mode & Effects Analysis (FMEA)

Selection criteria: detectable by sensor signal with adequate lead time (minimum 6 hours), severity score ≥ 6, occurrence probability ≥ 2 per machine per year.

| ID | Component | Failure Mode | Root Cause | Detectable Signal | Lead Time | Severity | Occurrence | Detection |
|----|-----------|--------------|------------|-------------------|-----------|----------|------------|-----------|
| FM-01 | Excavator swing gearbox | Gear tooth wear/spalling | Lubrication failure, overload | Vibration peak at gear mesh freq + oil temp | 48-120 hrs | 9 | 3 | Low (no sensor currently) |
| FM-02 | Dumper turbocharger | Bearing seizure | Oil contamination, over-speeding | Boost pressure drop + exhaust temp rise | 24-72 hrs | 8 | 4 | Medium (pressure sensor) |
| FM-03 | Dumper suspension strut | Seal blow-out, oil loss | Overload, rough terrain | Pressure drop + ride height deviation | 12-48 hrs | 6 | 6 | High (pressure transducer) |
| FM-04 | Conveyor belt | Splice failure/misalignment | Tensile overload, tracking fault | Belt tension deviation + lateral drift | 6-24 hrs | 9 | 5 | High (tension + drift sensors) |
| FM-05 | Conveyor drive motor | Bearing degradation | Contamination, fatigue | Vibration RMS increase + temperature rise | 72-168 hrs | 7 | 3 | Medium (vibration sensor) |
| FM-06 | Excavator hydraulic pump | Cavitation/seal wear | Fluid contamination, pressure spikes | Pressure ripple amplitude + flow rate drop | 48-96 hrs | 8 | 4 | Low (pressure transducer) |
| FM-07 | Conveyor idler rollers | Roller seizure | Corrosion, bearing fatigue | Vibration frequency shift | 24-96 hrs | 5 | 8 | Low (periodic manual check only) |

Severity scale: 1 (negligible) to 10 (catastrophic safety risk). Occurrence: estimated incidents per machine per year.

### 2.5 Cost Model

| Cost Element | Reactive | Scheduled | Predictive (AIPMS) | Saving vs Reactive |
|--------------|----------|-----------|--------------------|--------------------|
| Unplanned downtime cost (per incident) | Rs 8-15 Lakh | Rs 1-3 Lakh (partial) | Rs 0.2-0.5 Lakh (alert response) | Rs 7.5-14.5 Lakh/incident |
| Annual maintenance spend (per excavator) | Rs 1.2 Crore | Rs 80 Lakh | Rs 55 Lakh | Rs 65 Lakh/year/machine |
| Emergency spare parts premium | 30-50% above list price | 5-10% above list | List price (planned procurement) | 15-40% of parts cost |
| Safety incident liability | High (potential fatality) | Medium | Very Low | Unquantifiable |
| DGMS compliance fines (estimated) | Rs 2-10 Lakh/incident | Rs 0 | Rs 0 (proactive audit trail) | Full fine avoidance |

**Total Annual Savings = (Cost_Reactive - Cost_Predictive) × Fleet_Size**
**= (Rs 1.2 Cr - Rs 0.55 Cr) × 10 machines = Rs 6.5 Crore/year**
**ROI Period = System_Development_Cost / Annual_Savings = ~Rs 15 Lakh / Rs 6.5 Cr = 0.023 years (< 1 month)**

---

## 3. Stakeholders, User Personas & Use Cases

### 3.1 Stakeholder Register

| Stakeholder | Role | Stakes | Communication Need |
|-------------|------|--------|-------------------|
| Maintenance Engineer | Primary system user | Equipment uptime, job efficiency, safety | Daily alerts, RUL data, job instructions |
| Shift Supervisor | Shift operations | No production stoppages during shift | Shift handover report, risk overview |
| Plant / Colliery Manager | P&L accountability | Maintenance budget, production targets | Weekly KPI dashboard, cost trends |
| Safety Officer (DGMS compliance) | Regulatory compliance | Zero fatalities, DGMS inspection records | Critical alert log, compliance reports |
| Maintenance Technician | Field job execution | Clear, precise job instructions | Job detail card, parts list |
| Mine IT Administrator | System operation | System uptime, data security | Health dashboard, backup reports |
| CMMS/ERP System (SAP PM) | Downstream integration | Work order creation, inventory | Automated API push for maintenance jobs |

### 3.2 User Personas

#### Persona 1: Rajan Sharma — Senior Maintenance Engineer

| Attribute | Detail |
|-----------|--------|
| Background | Mechanical engineer (BE), 8 years at BCCL Patherdih area. Manages 12 machines across two production benches. Certified by DGMS for heavy equipment inspection. |
| Current frustration | Gets called at 2 AM when excavator breaks mid-shift. Emergency spares take 6 hours to arrive. Cannot plan technician rosters in advance. Feels reactive. |
| Primary goal | Know 3 days in advance which machine will need service, so he can schedule jobs during planned shift changeover (4:30–6 AM) without halting production. |
| AIPMS need | Alert feed with WHY (not just what) — top sensors, failure mode name. RUL gauge in days, not hours. One-click job dispatch to technicians. |
| Tech comfort | Comfortable with desktop web apps. Uses WhatsApp for team coordination. Will not read technical documentation — needs plain English alerts. |
| Success metric | Zero 2 AM emergency calls. Maintenance completion rate > 95% within planned windows. |

#### Persona 2: Sunita Prasad — Plant Manager

| Attribute | Detail |
|-----------|--------|
| Background | B.Tech + MBA, 15 years in Coal India operations. P&L responsibility for production output. Reports to Colliery GM. Under pressure to meet monthly dispatch targets. |
| Current frustration | Unplanned downtime destroys monthly production targets. Cannot justify maintenance budget to GM without data. Loses sleep over Sunday morning breakdowns. |
| Primary goal | One screen: which machines will fail this week? What is it going to cost if I ignore it? What do I need to do right now? |
| AIPMS need | Fleet KPI dashboard, 7-day risk forecast, downloadable PDF report for planning meetings, cost-vs-risk graph. |
| Tech comfort | Desktop user, comfortable with Excel exports. Wants print-friendly formats for GM presentations. |
| Success metric | Monthly production target achieved. Maintenance budget variance < 10%. Zero DGMS citations. |

### 3.3 User Stories with Acceptance Criteria

| ID | As a... | I want to... | Acceptance Criterion | Priority |
|----|---------|-------------|---------------------|----------|
| US-01 | Maintenance Engineer | See live status of all machines on one screen | Fleet overview loads < 3s; status badges green/amber/red; updates every 5s | Must Have |
| US-02 | Maintenance Engineer | Receive a 48-hour advance failure alert | Alert fires when failure_prob > 0.70 AND RUL < 72 hrs; includes top 3 sensors | Must Have |
| US-03 | Maintenance Engineer | Understand which sensor is causing an alert | SHAP top-3 sensors shown on every alert card with impact % and plain-English label | Must Have |
| US-04 | Shift Supervisor | Export shift handover status report | One-click CSV/PDF export of all equipment status with timestamp | Should Have |
| US-05 | Plant Manager | See 7-day maintenance cost forecast | Schedule screen shows estimated cost per job and total 7-day maintenance spend | Should Have |
| US-06 | Maintenance Engineer | View 30-day RUL degradation trend | Equipment detail shows RUL history chart with trend line and 95% CI band | Should Have |
| US-07 | Any user | Acknowledge alerts to clear alert feed | Acknowledge button moves alert to resolved section; audit log records user + time | Must Have |
| US-08 | Plant Manager | Download maintenance schedule as CSV | st.download_button generates schedule CSV with all columns within 2 clicks | Should Have |
| US-09 | Safety Officer | View all critical alerts in date range | Alert feed filterable by severity + date range; exportable for DGMS report | Should Have |
| US-10 | IT Admin | Check system health without opening DB | GET /health returns status of all 5 services + model load status in < 200ms | Must Have |

---

## 4. Requirements Specification

### 4.1 Functional Requirements

| ID | Requirement | Priority | PS-1 Mapping | Test Ref |
|----|------------|----------|--------------|----------|
| FR-01 | System shall ingest simulated sensor data at ≥ 1 Hz per sensor per equipment unit via MQTT | Must Have | IoT Architecture | UT-01 |
| FR-02 | System shall detect anomalies and classify as normal / warning / critical within 10s of sensor event | Must Have | Analytics | IT-02 |
| FR-03 | System shall predict failure probability within a 7-day horizon for each active equipment unit | Must Have | Analytics | IT-03 |
| FR-04 | System shall estimate RUL in hours for each equipment unit and update every 10 seconds | Must Have | Life Estimation | IT-04 |
| FR-05 | System shall generate a prioritized maintenance schedule using composite priority scoring | Must Have | Optimization | IT-05 |
| FR-06 | System shall display live fleet status, sensor trends, and alerts on a web dashboard | Must Have | Interface | E2E-01 |
| FR-07 | Dashboard shall refresh without manual reload within 5 seconds | Must Have | Interface | E2E-01 |
| FR-08 | Each alert shall include top 3 contributing sensor features with SHAP impact values | Must Have | Analytics | IT-06 |
| FR-09 | System shall allow alert acknowledgement with user ID and timestamp audit log | Should Have | Interface | IT-07 |
| FR-10 | System shall export maintenance schedule as CSV | Should Have | Interface | IT-08 |
| FR-11 | System shall store 30 days of prediction history per equipment for trend analysis | Should Have | Analytics | UT-09 |
| FR-12 | System shall support simultaneous simulation of ≥ 3 equipment units at different lifecycle stages | Must Have | Prototype Demo | E2E-02 |
| FR-13 | System shall flag data quality issues (missing readings, out-of-range values) in alert feed | Should Have | Data Quality | UT-10 |
| FR-14 | Dashboard shall provide a KPI summary screen for plant manager with fleet-level metrics | Should Have | Interface | IT-11 |

### 4.2 Non-Functional Requirements

| ID | Category | Requirement | Metric | Rationale |
|----|----------|------------|--------|-----------|
| NFR-01 | Performance | API p95 response time | < 200 ms | Engineer dashboard UX; Streamlit polling every 5s |
| NFR-02 | Performance | ML inference latency per equipment | < 100 ms | Allows 10 equipment units on single machine |
| NFR-03 | Performance | Dashboard initial load time | < 3 seconds | User patience threshold for web apps |
| NFR-04 | Availability | System uptime during evaluation | > 99% | Single machine; no HA needed for hackathon |
| NFR-05 | Scalability | Architecture supports 50+ equipment units | Documented in design | Post-hackathon growth path |
| NFR-06 | Reliability | Simulator reconnect after MQTT disconnect | < 10 seconds | Demo resilience |
| NFR-07 | Usability | Alert acknowledgement in < 3 clicks | Usability test | Emergency response efficiency |
| NFR-08 | Portability | Runs on standard laptop (Windows/Mac/Linux) | Python 3.10+, 8 GB RAM, no GPU | Judge reproducibility |
| NFR-09 | Maintainability | ML model swap without API contract change | Model abstraction layer | Future retraining agility |
| NFR-10 | Security | No sensor data leaves local network (prototype) | No external API calls in hot path | Data sovereignty |
| NFR-11 | Observability | All ML inference results logged with timestamp | 100% of inferences stored | Model monitoring and drift detection |
| NFR-12 | Auditability | Alert acknowledgements immutably logged | acknowledged_by + timestamp required | DGMS compliance |

---

## 5. System Architecture

### 5.1 Architectural Principles

1. **Separation of Concerns**: Each layer has exactly one responsibility
2. **Data Contract First**: All ML inference operates on well-defined, clean, normalized feature vector
3. **Graceful Degradation**: If ML inference fails, dashboard still renders raw sensor data
4. **Explainability by Design**: Every alert carries evidential basis (SHAP top-3 sensors)
5. **Prototype-to-Production Path**: Every technology choice has documented production equivalent
6. **Observability**: Every inference output is persisted for model monitoring

### 5.2 System Context

AIPMS sits between the physical mining equipment layer and the human decision layer. It has three external integration points:

| External System | Integration Type | Data Direction | Prototype Status |
|-----------------|-----------------|----------------|-----------------|
| Mining equipment sensors | MQTT IoT stream (simulated in prototype) | Sensors → AIPMS | Python simulator replaces hardware |
| Engineer web browser | HTTP / WebSocket | AIPMS → Engineer | Streamlit serves at localhost:8501 |
| CMMS / SAP PM (future) | REST API push | AIPMS → SAP PM work orders | Documented API endpoint; stub implementation |
| DGMS compliance system (future) | Scheduled PDF/CSV export | AIPMS → DGMS report | Export endpoint implemented in prototype |

### 5.3 Five-Layer Architecture

| Layer | Name | Prototype Technology | Production Technology | Responsibility |
|-------|------|---------------------|----------------------|----------------|
| L1 | Physical Equipment | Python simulator (3 equipment units) | IoT hardware sensors (ADXL345, PT100, CT clamps) | Source of all sensor telemetry |
| L2 | IoT Edge | Python paho-mqtt publisher | Raspberry Pi edge nodes with Mosquitto edge broker | Collect sensor readings, publish to broker |
| L3 | Data Ingestion & Storage | Mosquitto broker + SQLite + paho-mqtt subscriber | AWS IoT Core + InfluxDB + TimescaleDB | Receive, validate, store sensor stream |
| L4 | AI/ML Core | scikit-learn + PyTorch + FastAPI + APScheduler | FastAPI on ECS Fargate + SageMaker inference | Preprocess, infer, generate alerts, optimize schedule |
| L5 | Dashboard & Interface | Streamlit + Plotly | Grafana + React or Streamlit Enterprise | Engineer-facing UI, KPI reporting, alert management |

### 5.4 Data Flow — Sequence Description

The complete data journey from sensor event to engineer action:

1. Python simulator generates a realistic sensor reading (e.g., excavator vibration = 4.2 mm/s) with ISO-8601 timestamp, equipment ID, and sensor name.
2. Simulator publishes JSON payload to MQTT broker on topic: `mines/equipment/EXC-01/sensors` (QoS level 1 — at-least-once delivery).
3. Mosquitto broker routes message to all subscribers. MQTT subscriber daemon receives, validates JSON schema, rejects malformed messages (data quality guard).
4. Valid readings written to SQLite table `sensor_readings`. Out-of-range values are written with `data_quality_flag = 'suspect'` and trigger a separate data quality alert.
5. FastAPI APScheduler background job fires every 10 seconds: reads last 5-minute window from DB per equipment, preprocesses (normalize, compute rolling features), runs all 3 ML models.
6. Model outputs (anomaly_score, failure_prob, rul_hours, top_features_json) written to `predictions` table. If anomaly_label changed from previous cycle, insert into `alerts` table.
7. Maintenance scheduler fires every 15 minutes: reads latest predictions for all equipment, computes priority scores, updates `maintenance_jobs` table.
8. Streamlit dashboard polls `GET /equipment` (summary) every 5 seconds. On status change to critical/warning, flashes red banner at top of screen.
9. Engineer clicks alert card, reads SHAP attribution, dispatches technician. Clicks Acknowledge — audit record written with engineer_id and timestamp.
10. Scheduled daily job generates DGMS-format equipment condition PDF and stores in `/reports/` directory; accessible via `GET /reports/latest`.

### 5.5 Component Interaction Architecture

**L2 → L3: IoT to Data Layer**
```
Simulator.py  ──[MQTT publish, QoS 1]──>  Mosquitto:1883  ──[MQTT subscribe]──>  mqtt_subscriber.py
Payload: { equipment_id:str, timestamp:ISO8601, sensor_name:str, value:float, unit:str }
Error handling: malformed JSON → log + discard; out-of-range value → store with quality_flag=suspect
Reconnect: paho-mqtt auto-reconnect with exponential backoff (max 30s)
```

**L3 → L4: Data to ML Layer**
```
mqtt_subscriber.py  ──[SQLAlchemy write]──>  sensor_readings table
FastAPI APScheduler  ──[SQLAlchemy read, last 300 rows per equipment]──>  inference_service.py
inference_service.py  ──[write]──>  predictions table + alerts table
Trigger: APScheduler interval job every 10 seconds
Failure mode: if model raises exception → log error + write last_known prediction with staleness_flag=True
```

**L4 → L5: ML to Dashboard Layer**
```
Streamlit  ──[HTTP GET /equipment]──>  FastAPI:8000  (polling interval: 5 seconds)
Streamlit  ──[HTTP GET /alerts?severity=warning,critical&acknowledged=false]──>  FastAPI:8000
Streamlit  ──[HTTP GET /schedule?days=7]──>  FastAPI:8000
Streamlit  ──[HTTP GET /dashboard/kpi]──>  FastAPI:8000
FastAPI response time target: p95 < 200ms; p99 < 500ms
```

**L4 → External: CMMS Integration (Production)**
```
FastAPI scheduler  ──[HTTP POST]──>  SAP PM REST API  (create work order on Critical alert)
Payload: { equipment_id, failure_mode, priority, recommended_action, rul_hours, due_date }
Prototype: endpoint documented at POST /integrations/cmms/work-order; stub implementation
Authentication: OAuth 2.0 client credentials (SAP PM API key stored in environment variable)
```

---

## 6. Data Design

### 6.1 Dataset

| Attribute | Detail |
|-----------|--------|
| Primary Dataset | NASA C-MAPSS Turbofan Engine Degradation Simulation Dataset |
| Source | NASA Prognostics Center of Excellence — public domain, no license restrictions |
| Subsets Used | FD001 (single operating condition, single fault) + FD003 (single condition, two faults) |
| Training Size | FD001: 20,631 rows / 100 engines; FD003: 24,720 rows / 100 engines |
| Active Features | 14 sensors after removing 7 near-zero-variance columns (sensors 1,5,6,10,16,18,19) |
| Mining Analogy | Turbofan engine degradation maps to motor/engine degradation in mining equipment |
| Simulator | Python-generated synthetic data with mining sensor names for live demo realism |

### 6.2 Active Sensor Features & Mapping

| Feature | Physical (C-MAPSS) | Mining Equivalent | Units | Failure Indicator | Active |
|---------|-------------------|-------------------|-------|-------------------|--------|
| op_setting_1 | Flight altitude/load | Machine load/haul grade | — | Context | Yes |
| op_setting_2 | Mach number | Operating speed setting | — | Context | Yes |
| sensor_2 (T24) | LPC outlet temperature | Engine block temperature | °C | Rises before turbo failure | Yes |
| sensor_3 (T30) | HPC outlet temperature | Hydraulic fluid temperature | °C | Rises with pump wear | Yes |
| sensor_4 (T50) | LPT outlet temperature | Exhaust temperature | °C | Rises near EOL | Yes |
| sensor_7 (P30) | HPC outlet pressure | Hydraulic system pressure | bar | Drops with seal wear | Yes |
| sensor_8 (Nf) | Physical fan speed | Primary RPM | RPM | Erratic near failure | Yes |
| sensor_9 (Nc) | Core speed | Secondary shaft RPM | RPM | Load correlation | Yes |
| sensor_11 (Ps30) | Static pressure | Boost/intake pressure | kPa | Drops with turbo degradation | Yes |
| sensor_12 (ratio) | Fuel-air ratio | Fuel consumption rate | L/hr | Spikes with combustion issues | Yes |
| sensor_13 (BPR) | Bypass ratio | Ventilation ratio | — | Anomalous near failure | Yes |
| sensor_14 (farB) | Burner fuel-air ratio | Secondary fuel parameter | — | Secondary signal | Yes |
| sensor_15 (htBleed) | Bleed enthalpy | Hydraulic bleed pressure | kPa | Pressure integrity proxy | Yes |
| sensor_17 (phi) | Corrected fan speed | Vibration-related speed deviation | RPM | Increases with bearing wear | Yes |
| sensors 1,5,6,10,16,18,19 | Various | N/A — removed | — | Near-zero variance in FD001 | No |

### 6.3 Feature Engineering Pipeline

**Step 1 - RUL Label**:
```
RUL[engine_id, cycle] = max_cycle[engine_id] - current_cycle
RUL_clipped = min(RUL, 125)  // Piecewise linear target — flat early, then linear decline
```

**Step 2 - Min-Max Normalization**:
```
x_norm = (x - min_train) / (max_train - min_train + epsilon)
```
Scaler fitted on training set only. Saved as MinMaxScaler.pkl for consistent application. epsilon = 1e-8 prevents division by zero.

**Step 3 - Rolling Statistics (Window = 5 cycles / 30 seconds)**:

| Feature Name | Formula | Window | Output Dimensions | Purpose |
|--------------|---------|--------|-------------------|---------| 
| rolling_mean_s{k} | mean(sensor_k[-w:]) | 5 cycles | 14 features | Smooths noise, trend direction |
| rolling_std_s{k} | std(sensor_k[-w:]) | 5 cycles | 14 features | Variability increase near failure |
| rolling_slope_s{k} | linregress(t[-w:], sensor_k[-w:]).slope | 5 cycles | 14 features | Rate of change (1st derivative) |

Total XGBoost feature vector: 14 (raw) + 14 (mean) + 14 (std) + 14 (slope) = **56 features**

**Step 4 - Binary Failure Label**:
```
failure_label = 1 if RUL <= 30 cycles else 0
```
30-cycle horizon ≈ 7 simulated days. Class ratio in FD001 training set: ~3.5:1 (negative:positive).

**Step 5 - LSTM Sequence Construction**:
```
X_lstm.shape = (num_samples, 50, 14)  // 50 time steps, 14 active sensor features
```
Sequences shorter than 50 steps zero-padded on the left.

### 6.4 Database Schema

#### Table: equipment
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(10) | PK, NOT NULL | Equipment identifier (e.g., EXC-01, DMP-03, CVR-01) |
| name | VARCHAR(100) | NOT NULL | Human-readable name |
| type | VARCHAR(20) | NOT NULL, CHECK IN (excavator,dumper,conveyor,drill) | Equipment class |
| location | VARCHAR(100) | NOT NULL | Mine bench/section |
| commissioned_date | DATE | | Date of first operation |
| total_operating_hours | FLOAT | DEFAULT 0 | Cumulative operating hours |
| status | VARCHAR(10) | DEFAULT 'normal' | Current status: normal/warning/critical/offline |
| last_updated | DATETIME | NOT NULL | Timestamp of last status update |

#### Table: sensor_readings
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Row identifier |
| equipment_id | VARCHAR(10) | FK → equipment.id, NOT NULL | Which machine |
| timestamp | DATETIME | NOT NULL | ISO-8601 UTC timestamp of reading |
| sensor_name | VARCHAR(50) | NOT NULL | Sensor identifier |
| value | FLOAT | NOT NULL | Raw sensor reading |
| unit | VARCHAR(20) | NOT NULL | Engineering unit (°C, mm/s, bar, RPM, A, L/hr) |
| data_quality_flag | VARCHAR(10) | DEFAULT 'ok' | ok/suspect/missing |

#### Table: predictions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Row identifier |
| equipment_id | VARCHAR(10) | FK → equipment.id, NOT NULL | Which machine |
| timestamp | DATETIME | NOT NULL | When inference was run |
| anomaly_score | FLOAT | CHECK 0<=x<=1 | Isolation Forest anomaly score |
| anomaly_label | VARCHAR(10) | CHECK IN (normal,warning,critical) | Thresholded label |
| failure_prob | FLOAT | CHECK 0<=x<=1 | XGBoost 7-day failure probability |
| rul_hours | FLOAT | CHECK x>=0 | LSTM RUL estimate in hours |
| rul_confidence_low | FLOAT | | Lower bound of 95% confidence interval |
| rul_confidence_high | FLOAT | | Upper bound of 95% confidence interval |
| top_features_json | TEXT | | JSON array: [{sensor, shap_value, impact_pct}] x 5 |
| model_version | VARCHAR(20) | NOT NULL | Version of models used |

#### Table: alerts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Row identifier |
| equipment_id | VARCHAR(10) FK | Which machine triggered the alert |
| triggered_at | DATETIME NOT NULL | When alert was generated |
| severity | VARCHAR(10) NOT NULL | warning/critical |
| message | TEXT NOT NULL | Plain-English alert message |
| top_sensors | TEXT | JSON: top 3 SHAP sensors with impact values |
| failure_mode_hint | VARCHAR(100) | ML-inferred likely failure mode from FMEA mapping |
| acknowledged | BOOLEAN DEFAULT 0 | Whether engineer has acknowledged |
| acknowledged_at | DATETIME | Timestamp of acknowledgement |
| acknowledged_by | VARCHAR(50) | Engineer ID/name |
| resolved_at | DATETIME | When alert condition cleared |

#### Table: maintenance_jobs
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Row identifier |
| equipment_id | VARCHAR(10) FK | Target equipment |
| created_at | DATETIME | When job was generated by scheduler |
| priority_score | FLOAT 0-1 | Composite priority score |
| priority_tier | VARCHAR(10) | critical/warning/normal |
| failure_prob | FLOAT | failure_prob at time of scheduling |
| rul_hours | FLOAT | RUL at time of scheduling |
| recommended_action | TEXT | Plain-English action |
| estimated_duration_hours | FLOAT | Estimated technician-hours required |
| parts_required | TEXT | JSON list of parts to pre-order |
| scheduled_window_start | DATETIME | Recommended maintenance window start |
| scheduled_window_end | DATETIME | Recommended maintenance window end |
| status | VARCHAR(20) | scheduled/in_progress/completed/deferred |
| cmms_work_order_id | VARCHAR(50) | SAP PM work order ID |
| notes | TEXT | Additional engineer notes |

#### Table: model_metadata
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Row identifier |
| model_name | VARCHAR(50) UNIQUE | anomaly_detector / failure_predictor / rul_estimator |
| version | VARCHAR(20) | Semantic version (e.g., 1.0.0) |
| trained_at | DATETIME | Training completion timestamp |
| dataset | VARCHAR(50) | Training dataset name and subset (e.g., C-MAPSS FD001) |
| n_train_samples | INTEGER | Number of training samples |
| rmse | FLOAT | RMSE on validation set (RUL estimator only) |
| auc_roc | FLOAT | AUC-ROC on validation set (failure predictor only) |
| f1_score | FLOAT | F1-score on validation set (anomaly detector only) |
| nasa_score | FLOAT | NASA asymmetric score (RUL estimator only) |
| feature_list_json | TEXT | JSON array of feature names in order |
| hyperparams_json | TEXT | JSON dict of all hyperparameters used |
| file_path | VARCHAR(200) | Path to serialized model file (.pkl or .pt) |

---

## 7. Machine Learning Models

### 7.1 Model Comparison Study

Before selecting algorithms, candidate approaches were evaluated against: (1) suitability for multivariate time-series sensor data, (2) inference speed < 100ms, (3) explainability.

| Algorithm | Type | Strengths | Weaknesses | Selected? |
|-----------|------|-----------|-----------|-----------|
| Isolation Forest | Unsupervised anomaly | Fast, no labels needed, handles high-dim data well | No explanation for score (SHAP needed separately) | YES — M1 |
| DBSCAN | Unsupervised anomaly | Density-based, finds irregular shapes | Sensitive to epsilon/min_samples; slow on streaming | No |
| Autoencoder (LSTM) | Unsupervised anomaly | Learns complex sensor correlations | Requires GPU, slower inference, harder to tune | Stretch goal |
| One-Class SVM | Unsupervised anomaly | Solid mathematical basis | Very slow on high-dim data; no probability output | No |
| XGBoost | Supervised classification | Fast, tabular-native, built-in feature importance, SHAP compatible | Requires labeled data; point-in-time features only | YES — M2 |
| Random Forest | Supervised classification | Robust, interpretable | Slower inference than XGBoost; no gradient optimization | Baseline only |
| LightGBM | Supervised classification | Faster than XGBoost on large data | Less community documentation; similar accuracy | Fallback for M2 |
| Logistic Regression | Supervised classification | Very fast, fully interpretable | Linear — cannot capture sensor interaction effects | No |
| LSTM | Supervised regression | Captures temporal degradation trajectory | Requires GPU for training; slower than tree models | YES — M3 |
| CNN-LSTM | Supervised regression | Local + global temporal patterns | More complex; marginal improvement over LSTM | Stretch goal |
| XGBoost Regressor | Supervised regression | Fast fallback if LSTM training fails | Does not model temporal dependencies | Fallback for M3 |
| Prophet | Time-series forecasting | Good for trend + seasonality | Not designed for anomaly/failure prediction | No |

### 7.2 Alternative Architectures Considered

| Architecture Option | Description | Why Rejected / Not Selected |
|--------------------|-------------|------------------------------|
| Single monolithic model | One neural network outputs anomaly + failure prob + RUL simultaneously | Harder to maintain, explain, and retrain independently. One model failure kills all outputs. |
| Rule-based threshold system | Flag sensors that exceed hard-coded thresholds | Brittle — cannot adapt to gradual drift. No RUL estimation. High false positive rate. |
| Online learning (streaming ML) | River or Vowpal Wabbit — model updates in real-time from stream | Complex to validate; concept drift can degrade model unpredictably; overkill for hackathon timeline. |
| Cloud ML pipeline (no local) | Train on SageMaker, inference via cloud endpoint | Internet dependency creates demo risk. Latency > 200ms. Not viable for intermittent mine connectivity. |
| Graph Neural Network | Model sensor relationships as a graph | State of the art but requires custom architecture; 3x training time; not reproducible in hackathon. |
| **Selected: 3 independent models** | **Isolation Forest + XGBoost + LSTM** | **Best balance of accuracy, explainability, training speed, and independence.** |

### 7.3 Model 1 - Anomaly Detection (Isolation Forest)

**Algorithm**: Isolation Forest builds an ensemble of random isolation trees. Anomalous points require fewer splits to isolate (shorter average path length). The anomaly score is a normalized inverse of this path length.

**Input/Output**:
- **Input**: 42-dimensional feature vector: [mean, std, slope] × 14 active sensors over a 30-second rolling window
- **Output**: anomaly_score ∈ [0,1]; anomaly_label: normal (< 0.40), warning (0.40-0.70), critical (> 0.70)
- **Training data**: First 60% of each engine's lifecycle in FD001 training set (healthy baseline period only)

**Hyperparameters**:
| Parameter | Value | Justification |
|-----------|-------|---------------|
| n_estimators | 200 | Stable score estimates; < 2% variance between runs |
| max_samples | 256 | Standard subsampling for tabular data |
| contamination | 0.05 | 5% assumed early-degradation contamination |
| max_features | 1.0 | Use all features per split - reduces variance |
| random_state | 42 | Reproducibility |
| Anomaly threshold (normal/warning) | 0.40 | Precision > 0.80 on warning class |
| Anomaly threshold (warning/critical) | 0.70 | False positive rate < 5% |

### 7.4 Model 2 - Failure Prediction (XGBoost Classifier)

**Input/Output**:
- **Input**: 56-dimensional feature vector: 14 raw sensors + 42 rolling statistics
- **Label**: Binary: 1 = failure within 30 cycles (≈ 7 days), 0 = healthy
- **Output**: failure_prob ∈ [0,1] (calibrated via Platt scaling); SHAP values for top-5 features

**Hyperparameters**:
| Parameter | Search Range | Optimal Value | Method |
|-----------|-------------|---------------|---------| 
| n_estimators | 100-500 | 300 | Early stopping on validation AUC (patience = 50 rounds) |
| max_depth | 3-8 | 5 | GridSearchCV; captures 3-way sensor interactions |
| learning_rate (eta) | 0.01-0.30 | 0.05 | Lower = better generalization |
| subsample | 0.6-1.0 | 0.8 | Row subsampling reduces variance |
| colsample_bytree | 0.6-1.0 | 0.8 | Feature subsampling per tree |
| min_child_weight | 1-10 | 3 | Minimum sum of instance weights |
| gamma | 0-5 | 0.1 | Minimum loss reduction for split |
| scale_pos_weight | computed | 3.5 | neg_count / pos_count: handles class imbalance |
| eval_metric | — | aucpr | AUC-PR more informative for imbalanced classes |
| tree_method | — | hist | Fast histogram-based algorithm |

**SHAP Integration**: SHAP (SHapley Additive exPlanations) computes marginal contribution of each feature to model output using game-theoretic Shapley values.

**Sample SHAP Attribution**:
```
ALERT: Excavator EXC-01 │ Failure probability: 78% │ Predicted failure: within 5 days
Recommended action: Schedule hydraulic pump inspection within 24 hours

Contributing factors (SHAP attribution):
  1. rolling_std_sensor_4 (HPC temp variability)      SHAP +0.42  →  Temperature fluctuating 3x baseline
  2. rolling_slope_sensor_7 (hydraulic pressure trend) SHAP +0.31  →  Pressure declining -2.1 bar/hr
  3. sensor_17 (speed deviation)                       SHAP +0.19  →  RPM 8% below rated at current load
  4. rolling_mean_sensor_8 (mean RPM)                  SHAP -0.08  →  (stabilizing factor)

Likely failure mode: FM-06 — Hydraulic pump cavitation / seal wear (FMEA Severity 8)
```

### 7.5 Model 3 - RUL Estimation (LSTM Regression)

**Network Architecture**:

| Layer | Type | Config | Output Shape | Purpose |
|-------|------|--------|--------------|---------| 
| Input | Sequence | 50 steps × 14 features, zero-padded | (B, 50, 14) | Temporal sensor history |
| BatchNorm | Normalization | Across feature dimension | (B, 50, 14) | Stabilizes training |
| LSTM-1 | Recurrent | 64 units, return_sequences=True, dropout=0.2 | (B, 50, 64) | Local degradation patterns |
| LSTM-2 | Recurrent | 32 units, return_sequences=False, dropout=0.2 | (B, 32) | Global trajectory learning |
| Dense-1 | Fully connected | 16 units, ReLU activation | (B, 16) | Non-linear RUL mapping |
| Dense-2 (Output) | Fully connected | 1 unit, ReLU activation | (B, 1) | RUL ≥ 0 enforced by ReLU |

**Training Configuration**:
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Loss function | Asymmetric weighted MSE | Late predictions penalized 1.5×; safer to over-predict urgency |
| RUL target clipping | min(RUL, 125) | Piecewise linear: flat at 125, linear decline |
| Optimizer | Adam, lr=0.001 | Adaptive learning rate; best for LSTM |
| LR scheduler | ReduceLROnPlateau(patience=5, factor=0.5) | Reduces lr when validation RMSE plateaus |
| Batch size | 256 | Stable gradient estimates; fits in 8GB RAM without GPU |
| Max epochs | 100 | Early stopping callback overrides if no improvement |
| Early stopping | patience=10, restore_best_weights=True | Prevents overfitting |
| Validation split | 20% by engine ID | Full engine lifecycles held out - prevents data leakage |
| Framework | PyTorch 2.0+ (or Keras fallback) | Flexible, production-grade |

**Asymmetric Loss Function**:
```
L(y, y_hat) = mean( w_i * (y_hat_i - y_i)^2 )

w_i = 1.5  if  y_hat_i > y_i   [overestimate: dangerous]
w_i = 1.0  if  y_hat_i <= y_i  [underestimate: conservative, safe]
```

**Confidence Intervals**:
Bootstrap ensemble of 10 LSTM models (same architecture, different random seeds) produces distribution of RUL predictions.
```
RUL_CI_95 = [percentile_2.5(ensemble_predictions), percentile_97.5(ensemble_predictions)]
```

**Evaluation Metrics**:
| Metric | Formula | Target (FD001) | Benchmark (literature) | Interpretation |
|--------|---------|----------------|------------------------|----------------|
| RMSE | sqrt(mean((y_hat - y)^2)) | < 20 cycles | ~13-18 cycles | Primary accuracy metric |
| MAE | mean(│y_hat - y│) | < 15 cycles | ~10-14 cycles | Average absolute error |
| R² | 1 - SS_res/SS_tot | > 0.85 | ~0.87-0.92 | Variance explained |
| NASA Score | Σ(exp(-e/13)-1 if e<0 else exp(e/10)-1) | < 300 | ~200-400 | Asymmetric: late penalty 3× early penalty |

### 7.6 Model 4 - Maintenance Scheduling Optimizer

**Optimization Problem Statement**:
```
Minimize:  E[Production_Loss] = Σ_i  P_failure(i) × Cost_failure(i) × Scheduling_Delay(i)

Subject to:
  Constraint 1 (Capacity):   Σ jobs_per_shift ≤ max_technician_capacity = 2
  Constraint 2 (Production): conveyor_maintenance ONLY during shift_changeover(t)
  Constraint 3 (Dependency): if EXC-01 critical AND DMP-01 critical → schedule EXC-01 first
  Constraint 4 (Parts):      flag job as HOLD if required_part NOT IN stock
```

**Priority Scoring Formula**:
```
Priority_Score(i) = w1 × P_failure(i) + w2 × Anomaly_Score(i) + w3 × (1 - RUL_norm(i))

where:  w1 = 0.50,  w2 = 0.30,  w3 = 0.20
and:    RUL_norm(i) = min(RUL_hours(i), 168) / 168   [normalize to 1-week horizon]
```

**Weight rationale**: Failure probability dominates (50%) as it directly predicts production loss. Anomaly score (30%) captures current sensor abnormality. RUL (20%) provides long-range view even when short-term probability is moderate.

**Classification & Action Mapping**:

| Priority Score | Tier | Action | Window | Escalation |
|---------------|------|--------|--------|------------|
| 0.75 - 1.00 | Critical | Immediate inspection required | Within 24 hours; next shift changeover | Auto-create SAP PM work order; notify Shift Supervisor |
| 0.50 - 0.75 | Warning | Schedule within 72 hours | Next available planned window | Alert in dashboard; send to Maintenance Engineer queue |
| < 0.50 | Normal | Follow standard service interval | Per original PM schedule | No change; continue monitoring |

**Cost-Minimization Logic**:
```
Optimal_Window(i) = argmin_t [ Cost_Maintenance(t) + E[Cost_Failure_Before_t] ]

where: E[Cost_Failure_Before_t] = P(failure before t) × Cost_Failure
       P(failure before t) = 1 - exp(-RUL_hazard_rate × t)   [exponential hazard model]
```

---

## 8. Data Quality & Model Governance

### 8.1 Data Quality Framework

| Quality Issue | Detection Method | Action | Alert Generated? |
|---------------|------------------|--------|-----------------|
| Missing reading (gap > 30s) | Timestamp gap detection in subscriber | Insert NULL row with quality_flag=missing; use last-known value with staleness flag | Yes - Data Quality Warning |
| Out-of-range value | Compare to sensor min/max | Store with quality_flag=suspect; exclude from rolling statistics | Yes - Data Quality Warning |
| Stuck sensor (constant value > 60s) | std(last 60 readings) < 0.001 | Flag as quality_flag=stuck; likely sensor failure | Yes - Sensor Failure Alert |
| Duplicate timestamp | Check unique constraint | Discard duplicate; log warning | No |
| JSON schema violation | Pydantic validation | Discard message; log malformed payload | No (logged only) |
| Implausible rate of change | │Δvalue/Δt│ > max_rate | Store with quality_flag=spike; flag for review | Yes if persists > 10s |

### 8.2 Model Drift Detection

| Drift Type | Detection Method | Trigger Threshold | Response |
|-----------|------------------|-------------------|----------|
| Feature drift (input distribution) | KS test on rolling 7-day sensor distribution vs training | KS p-value < 0.05 for ≥ 3 sensors | Log drift warning; flag predictions; notify for retraining |
| Prediction drift (output shift) | Monitor rolling 7-day mean failure_prob and anomaly_score | Mean failure_prob > 0.60 for 7 days (no failures observed) | Recalibrate XGBoost probability outputs using isotonic regression |
| RUL accuracy drift | Compare predicted RUL vs actual replacement dates | RMSE > 35 cycles on recent data | Trigger retraining pipeline; deploy new model version |
| Concept drift | Monitor false positive rate from alert acknowledgements | False positive rate > 15% over 30 days | Review FMEA thresholds; consider feature engineering updates |

### 8.3 Model Card

**Model Card: Failure Predictor v1.0**

| Attribute | Detail |
|-----------|--------|
| Model type | XGBoost binary classifier (gradient boosted decision trees) |
| Training data | NASA C-MAPSS FD001 + FD003 training sets (36,351 combined rows, 200 engines) |
| Target variable | Failure within 30 cycles (binary label) |
| Features | 56-dimensional: 14 raw sensors + 42 rolling statistics |
| Performance (validation) | AUC-ROC: 0.87 │ F1: 0.81 │ Precision: 0.79 │ Recall: 0.83 |
| Known limitations | Trained on turbofan data — requires distribution shift adaptation for real mining sensors |
| Bias considerations | Class imbalance handled by scale_pos_weight; slight over-prediction of failures (conservative — intentional) |
| Update frequency | Retrain when false positive rate exceeds 15% or new labeled data available |
| Owner | Team AIPMS — contact via GitHub repository |
| License | Model weights: MIT License. Training data: NASA public domain. |

### 8.4 Model Retraining Pipeline

1. **Trigger**: drift detection threshold exceeded OR new labeled data available OR scheduled quarterly retrain
2. **Data preparation**: Export last 90 days of sensor_readings + manual failure labels
3. **Train new model versions** on combined C-MAPSS + real data (transfer learning)
4. **Evaluate on holdout**: must exceed current model AUC by ≥ 0.01 to qualify for deployment
5. **Shadow deployment**: run new model in parallel for 48 hours; compare outputs
6. **Promotion**: if shadow model performance confirmed, swap model file, update model_metadata
7. **Rollback**: if new model generates > 20% more false positives in first week, auto-rollback

---

## 9. API Design

### 9.1 Architecture Overview
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn on port 8000
- **Documentation**: Auto-generated OpenAPI at http://localhost:8000/docs
- **Response format**: application/json with UTF-8 encoding

### 9.2 Complete Endpoint Specification

| Method | Endpoint | Summary | Auth (Prod) | Response |
|--------|----------|---------|-------------|----------|
| GET | /equipment | List all equipment with current ML status | API Key | Array of equipment status objects |
| GET | /equipment/{id} | Single equipment detail + latest prediction | API Key | Equipment + prediction + sensor snapshot |
| GET | /equipment/{id}/sensors | Recent sensor readings (default: last 100) | API Key | Array of {timestamp, sensor_name, value, unit, quality_flag} |
| GET | /equipment/{id}/predictions | Prediction history for trend charts | API Key | Array of {timestamp, anomaly_score, failure_prob, rul_hours} |
| GET | /equipment/{id}/rul | Latest RUL with confidence interval | API Key | {rul_hours, rul_cycles, ci_low, ci_high, staleness_flag} |
| GET | /alerts | Filtered alert list | API Key | Array of alert objects; supports ?severity=&acknowledged=&days= |
| POST | /alerts/{id}/acknowledge | Acknowledge an alert | API Key + User JWT | {ok, acknowledged_at, acknowledged_by} |
| GET | /schedule | Prioritized maintenance job list | API Key | Array of job objects; supports ?days=&tier= |
| GET | /dashboard/kpi | Fleet KPI summary for plant manager screen | API Key | {total_equip, critical, warning, normal, alerts_today, est_cost_7day} |
| GET | /dashboard/summary | Lightweight overview for fleet screen | API Key | Reduced equipment array for fast polling |
| POST | /integrations/cmms/work-order | Push critical job to CMMS (SAP PM stub) | API Key + CMMS Key | {cmms_work_order_id, status} |
| GET | /reports/latest | Download latest DGMS compliance report | API Key | PDF file download |
| GET | /health | Full system health check | None (public) | { api, db, mqtt_broker, models, uptime_sec } |

### 9.3 API Request/Response Examples

**GET /equipment - Response Example**:
```json
[
  {
    "id": "EXC-01",
    "name": "Rope Shovel #1 — North Bench",
    "type": "excavator",
    "status": "critical",
    "anomaly_score": 0.82,
    "anomaly_label": "critical",
    "failure_prob": 0.78,
    "rul_hours": 31.5,
    "rul_confidence_low": 18.2,
    "rul_confidence_high": 44.8,
    "last_updated": "2025-04-15T14:32:01Z",
    "top_features": [
      {"sensor": "rolling_std_sensor_4", "shap": 0.42, "pct": 45},
      {"sensor": "rolling_slope_sensor_7", "shap": 0.31, "pct": 33},
      {"sensor": "sensor_17", "shap": 0.19, "pct": 20}
    ]
  },
  { "id": "DMP-03", "status": "warning", "failure_prob": 0.54, "rul_hours": 89.0 },
  { "id": "CVR-01", "status": "normal", "failure_prob": 0.12, "rul_hours": 312.0 }
]
```

**POST /alerts/{id}/acknowledge - Request & Response**:
```json
// Request
POST /alerts/42/acknowledge
Headers: { "Authorization": "Bearer <engineer_jwt>", "Content-Type": "application/json" }
Body: { "acknowledged_by": "rajan.sharma" }

// Response HTTP 200
{ 
  "ok": true, 
  "alert_id": 42, 
  "acknowledged_at": "2025-04-15T14:35:22Z",
  "acknowledged_by": "rajan.sharma" 
}
```

**GET /health - Response Example**:
```json
{ 
  "api": "ok", 
  "db": "ok", 
  "mqtt_broker": "ok",
  "models": { 
    "anomaly_detector": "loaded_v1.0.0", 
    "failure_predictor": "loaded_v1.0.0",
    "rul_estimator": "loaded_v1.0.0" 
  },
  "uptime_sec": 3621, 
  "last_inference": "2025-04-15T14:31:55Z" 
}
```

### 9.4 MQTT Topic Schema

| Topic | Direction | Payload | QoS | Notes |
|-------|-----------|---------|-----|-------|
| mines/equipment/{id}/sensors | Simulator → Broker → DB | { equipment_id, timestamp, sensor_name, value, unit } | 1 (at-least-once) | 1 msg/sensor/second |
| mines/equipment/{id}/alerts | ML Engine → Broker | { severity, message, timestamp, top_sensors } | 1 | On status change only |
| mines/system/heartbeat | Simulator → Broker | { connected_units, uptime_sec, timestamp } | 0 (fire-and-forget) | Every 30 seconds |
| mines/system/data_quality | Subscriber → Broker | { equipment_id, sensor_name, flag, timestamp } | 1 | On quality flag event |

### 9.5 Error Handling

| Status | Condition | Response Body | Client Action |
|--------|-----------|---------------|---------------|
| 200 OK | Successful request | { data: ... } | Process normally |
| 400 Bad Request | Invalid parameter type | { error: 'severity must be warning or critical' } | Fix query params |
| 404 Not Found | Equipment ID does not exist | { error: 'Equipment EXC-99 not found' } | Check equipment ID |
| 422 Unprocessable | FastAPI schema validation failure | { detail: [ { loc, msg, type } ] } | Fix request body |
| 500 Internal Error | Model inference exception | { error: 'Inference failed', fallback: last_known_status } | Dashboard shows stale badge |
| 503 Unavailable | Models loading at startup | { error: 'Models loading', retry_after: 5 } | Retry after 5 seconds |

---

## 10. Dashboard Design

### 10.1 Design Principles
1. **Critical-First Information Hierarchy**: Red alerts always at top
2. **Engineer Vocabulary**: 'Days to Failure' not 'failure_prob'
3. **One Action Per Alert**: Every alert ends with concrete recommended action
4. **Progressive Disclosure**: Fleet overview → Equipment detail → Sensor trend
5. **Print-Ready Exports**: All screens have export functionality

### 10.2 Screen 1 - Fleet Overview (Home)

**Components**:
- **HEADER BAR**: Logo + mine name | KPI badges [Critical: N red] [Warning: N amber] [Healthy: N green] | Last refresh timestamp
- **EQUIPMENT CARD GRID** (3 columns):
  - Equipment icon + name + location
  - Status badge: CRITICAL (red) / WARNING (amber) / NORMAL (green)
  - Failure probability: horizontal bar chart 0-100%
  - RUL gauge: circular gauge (days remaining)
  - Top alert sensor: 'Main concern: Hydraulic pressure declining'
  - Last updated timestamp
- **SORT CONTROLS**: By severity (default) │ By RUL ascending │ By equipment type
- **REFRESH**: Auto every 5 seconds via st.rerun()

### 10.3 Screen 2 - Equipment Detail

**Sections**:
- **A - Identity Panel**: Equipment name │ Type │ Location │ Commissioned │ Total operating hours
- **B - Health Summary**: 4 metric gauges [Status Badge] [Anomaly Score] [Failure Prob] [RUL]
- **C - Live Sensor Trends**: Plotly line charts (last 10 minutes, 2 columns)
  - Temperature vs time with normal band + red threshold
  - Vibration RMS vs time with warning/critical thresholds
  - RPM vs time with rated RPM reference
  - Hydraulic pressure vs time with min/max normal band
- **D - SHAP Feature Attribution**: Horizontal bar chart — Top-5 sensors, SHAP value magnitude
- **E - RUL Trend**: 30-day history line chart with 95% CI band
- **F - Alert History**: Last 10 alerts with severity, message, timestamp, acknowledged status

### 10.4 Screen 3 - Plant Manager KPI Dashboard

**Components**:
- **TOP ROW - Fleet KPIs**: [Fleet Availability: 92%] [Alerts This Week: 7] [Critical Unacknowledged: 2] [Est. Maintenance Cost (7d): Rs 3.2L]
- **CENTRE - Risk Heatmap**: X-axis: 7 days; Y-axis: equipment; Color: failure_prob intensity (green→red)
- **CENTRE - Cost vs Risk Scatter**: X: Priority score; Y: estimated maintenance cost; bubble size: RUL
- **BOTTOM - 7-Day Maintenance Schedule Gantt**: Equipment on Y-axis; time on X-axis; bars = scheduled maintenance windows
- **EXPORT BUTTON**: Download KPI report as CSV │ Print-friendly layout toggle

### 10.5 Screen 4 - Maintenance Schedule

**Components**:
- **SCHEDULE TABLE** (sortable, filterable):
  - Columns: Rank │ Equipment │ Tier │ Action │ Window │ Est. Duration │ Parts Req. │ Status │ Cost
  - Row highlight: red = critical, amber = warning, white = normal
- **FILTER CONTROLS**: Equipment type │ Severity tier │ Date range │ Status
- **TECHNICIAN WORKLOAD VIEW**: Total scheduled hours per technician per shift
- **EXPORT**: CSV with all columns
- **PRINT**: Render print-optimized layout

### 10.6 Screen 5 - Alert Feed

**Components**:
- **ACTIVE ALERTS** (sorted by triggered_at descending):
  - Alert card per alert with CRITICAL/WARNING badge
  - Equipment name + type icon
  - Alert message (plain English)
  - SHAP top-3 sensors with plain labels and impact %
  - Failure mode hint from FMEA mapping
  - Recommended action (1 sentence)
  - Time since alert fired
  - [Acknowledge] button
- **DAILY SUMMARY BAR**: Total alerts today │ Avg time to acknowledge │ False positive rate (last 7d)
- **RESOLVED ALERTS** (collapsible): Last 50 acknowledged alerts; searchable

### 10.7 Alert Escalation Workflow

| Time Since Alert | Action | Mechanism |
|------------------|--------|-----------|
| 0 minutes | Alert appears in dashboard alert feed | Dashboard red badge + alert card |
| 30 minutes (unacknowledged) | Escalation: notify Shift Supervisor | Dashboard banner; optional SMS/email |
| 2 hours (unacknowledged) | Escalation: notify Plant Manager | Dashboard banner; CMMS work order auto-created |
| 4 hours (unacknowledged critical) | Final escalation: Safety Officer notified | Compliance alert logged; DGMS report flagged |
| Any time | Engineer acknowledges | Alert moved to resolved; escalation chain cancelled |

### 10.8 UI Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Streamlit | 1.32+ | Python-native, rapid iteration, no frontend code |
| Interactive charts | Plotly (st.plotly_chart) | 5.20+ | Gauges, time series, heatmaps, Gantt, scatter |
| API client | requests | 2.31+ | HTTP polling from Streamlit to FastAPI |
| Layout | st.columns, st.tabs, st.expander | Built-in | Multi-panel layouts without CSS |
| Real-time update | st.rerun() + time.sleep(5) | Built-in | 5-second polling auto-refresh |
| Data export | st.download_button + pandas | Built-in | CSV download for schedule and reports |
| Status display | st.metric() + st.markdown HTML | Built-in | Color-coded KPI cards |
| Sidebar navigation | st.sidebar + st.radio | Built-in | Screen switching without page reload |

---

## 11. IoT Architecture & Sensor Simulation

### 11.1 Production IoT Hardware BOM

| Component | Model | Per-Equipment Qty | Unit Cost (INR) | Purpose | Interface |
|-----------|-------|-------------------|-----------------|---------|-----------| 
| MEMS Accelerometer | Analog Devices ADXL345 | 2 | Rs 850 | Vibration (3-axis RMS) | I2C → Raspberry Pi |
| RTD Temperature Sensor | PT100 + MAX31865 amplifier | 3 | Rs 1,200 | Engine block, hydraulic fluid, exhaust temperature | SPI → Raspberry Pi |
| Pressure Transducer | Honeywell MLH series (0-300 bar) | 2 | Rs 4,500 | Hydraulic system pressure | 4-20mA → ADS1115 ADC → Pi |
| Hall Effect RPM Sensor | Allegro ATS667LSG | 1 | Rs 600 | Shaft/wheel RPM | Pulse count → Pi GPIO |
| CT Clamp (Current) | YHDC SCT-013 (100A) | 2 | Rs 400 | Motor current draw | Analog → ADS1115 → Pi |
| Flow Sensor | Gems Sensors FT-110 series | 1 | Rs 6,000 | Hydraulic fluid flow rate | Pulse → Pi GPIO |
| Edge Computing Node | Raspberry Pi 4B (4GB) | 1 | Rs 5,500 | Edge processing + MQTT publish | WiFi/Ethernet → mine network |
| Industrial Enclosure | IP67 DIN rail box | 1 | Rs 2,000 | Weatherproof housing | — |
| Power Supply | 24VDC DIN rail PSU (5A) | 1 | Rs 1,800 | Power all sensors + Pi | Mine 230V supply |
| 4G LTE Router (backup) | Quectel EC25 module | 1 | Rs 3,500 | Connectivity fallback | SIM card → MQTT over 4G |

**Total hardware cost per equipment unit**: Rs 26,500
**Full fleet of 10 machines**: Rs 2.65 Lakh
**System development and integration**: Rs 10-15 Lakh
**Total production deployment**: Rs 12-18 Lakh
**ROI**: < 1 month given Rs 6.5 Cr annual savings

### 11.2 Network Topology (Production)

| Network Zone | Components | Protocol | Security |
|--------------|------------|----------|----------|
| Equipment (Zone 1) | Sensors + Raspberry Pi edge node per machine | I2C, SPI, GPIO, 4-20mA | Physical access control; no internet access |
| Mine LAN (Zone 2) | Raspberry Pi → mine WiFi AP (WPA3) → Mosquitto broker | MQTT over TLS (port 8883) | WPA3 encryption; MQTT ACLs per device certificate |
| Server (Zone 3) | Mosquitto broker, FastAPI, SQLite, ML models | Local TCP; no internet required | Server room access control; firewall blocking inbound internet |
| Office (Zone 4) | Engineer/manager workstations → Streamlit dashboard | HTTPS (port 8501) with TLS | Role-based access; session timeout 4 hours |
| Cloud (Zone 5 - future) | AWS IoT Core, InfluxDB, SageMaker | MQTT over TLS + REST HTTPS | VPC isolation; IAM roles; KMS encryption |

### 11.3 Sensor Simulator Architecture (Prototype)

**Lifecycle Stages**:

| Lifecycle Stage | Lifecycle % | Temperature | Vibration | Hydraulic Pressure | RPM |
|-----------------|-------------|-------------|-----------|-------------------|-----|
| Healthy | 0-60% | Baseline ± 2% Gaussian noise | Baseline ± 2% noise | Baseline ± 1% noise | Rated ± 1% noise |
| Early degradation | 60-80% | Linear +5% drift | Linear +15% drift | Linear -3% drift | Linear -2% drift |
| Accelerated degradation | 80-95% | Exponential +20% rise | Exponential +40% rise | Exponential -15% drop | Erratic ±8% swings |
| Imminent failure | 95-100% | Near critical threshold | 3× baseline (spike events) | Near minimum threshold | Intermittent drop-outs |
| Failed | 100% | Flat at last value or 0 | Flat 0 (offline) | Flat 0 | 0 RPM |

**Demo Setup**:
- EXC-01 starts at 90% lifecycle (accelerated degradation → critical within 3 min)
- DMP-03 at 70% (early degradation → warning)
- CVR-01 at 30% (healthy)
- Ensures judges see all three states within first 5 minutes

### 11.4 Sensor Parameter Thresholds

| Sensor | Equipment | Normal Range | Warning Threshold | Critical Threshold | Unit | Failure Mode |
|--------|-----------|--------------|-------------------|-------------------|------|--------------|
| Engine temperature | Dumper | 70-95 | 105 | 115 | °C | FM-02: Turbocharger failure |
| Hydraulic fluid temp | Excavator | 40-65 | 75 | 85 | °C | FM-06: Pump cavitation |
| Vibration RMS | Excavator | 0.5-2.0 | 3.5 | 6.0 | mm/s | FM-01: Gearbox spalling |
| Hydraulic pressure | Excavator | 180-220 | 160 | 140 | bar | FM-06: Seal wear |
| Engine RPM | Dumper | 1200-1800 | <900 or >2100 | <700 or >2400 | RPM | FM-02: Engine fault |
| Belt tension | Conveyor | 8-12 | <6 or >14 | <4 or >16 | kN | FM-04: Splice failure |
| Motor current | Conveyor | 40-60 | 75 | 90 | A | FM-05: Bearing degradation |
| Fuel consumption | Dumper | 18-25 | 30 | 38 | L/hr | FM-02: Combustion fault |
| Boost pressure | Dumper | 1.4-2.2 | 1.1 | 0.8 | bar absolute | FM-02: Turbo failure |

---

## 12. Security, Privacy & Regulatory Compliance

### 12.1 Security Architecture

| Security Layer | Prototype | Production |
|----------------|-----------|------------|
| MQTT transport | Unencrypted (localhost only) | MQTT over TLS 1.3 (port 8883); CA-signed broker certificate |
| MQTT authentication | Anonymous (local) | Per-device X.509 certificates; ACL restricts topic write by device |
| API authentication | None (local) | JWT Bearer tokens (30-min expiry); API keys for service accounts |
| API authorization | None | RBAC: engineer (read + acknowledge), manager (read + export), admin (full) |
| Dashboard access | None (localhost) | OIDC/SSO (Google Workspace or Azure AD); session timeout 4 hrs |
| Data at rest | Unencrypted SQLite | SQLCipher (AES-256); key stored in AWS Secrets Manager |
| Audit logging | predictions + alerts tables | Immutable audit table: all actions logged with user + timestamp |
| Secrets management | Environment variables (.env file) | AWS Secrets Manager; no secrets in code or config files |

### 12.2 Privacy Design

- AIPMS processes **operational sensor data only** - no PII required
- Engineer IDs in alert acknowledgements are login usernames — can be pseudonymized
- No biometric, location, or personal health data collected
- Sensor data is mine-operational and proprietary — not personal data under DPDPA 2023
- Data retention: sensor_readings older than 90 days archived or deleted per mine data policy

### 12.3 Regulatory Compliance - DGMS

| Regulation | Requirement | AIPMS Response |
|------------|-------------|----------------|
| Coal Mines Regulations 2017, Reg 100(2) | Periodic inspection of winding engines, haulage, and transport equipment | AIPMS generates condition-based inspection records; provides sensor evidence for inspection log |
| DGMS Circular No. 3 of 2012 | Monitoring of conveyor belt systems, including tension and speed | CVR-01 conveyor monitoring: belt tension, speed deviation, motor current |
| DGMS Circular No. 8 of 2018 | Condition monitoring of major mining equipment | AIPMS implements continuous vibration, temperature, and pressure condition monitoring |
| Mines Act 1952, Section 22 | Manager responsible for maintenance of plant and machinery in safe working order | AIPMS provides manager with 7-day risk forecast and audit trail of maintenance actions |
| Coal Mines (Special Provisions) Rules 2017 | Production records and equipment availability reporting | AIPMS tracks fleet availability; generates production-impact reports |

**DGMS Compliance Report Feature**:
Daily DGMS-format equipment condition report containing:
- Equipment ID, type, location, current operating hours
- Condition status per sensor category (normal/warning/critical)
- Anomalies detected in past 24 hours with timestamps
- Maintenance actions completed in past 24 hours
- Upcoming maintenance due within 7 days
- Report signed with mine manager name and date

Available via: `GET /reports/latest` → PDF download
Auto-generated: daily at 06:00 mine time via APScheduler

---

## 13. Deployment Architecture

### 13.1 Prototype Deployment - 5-Service Local Stack

| Service | Start Command | Port | Health Check | Depends On |
|---------|---------------|------|--------------|------------|
| Mosquitto MQTT broker | mosquitto -c config/mosquitto.conf | 1883 | mosquitto_sub -t mines/system/heartbeat | None |
| MQTT DB writer | python simulator/mqtt_subscriber.py | — | Check sensor_readings row count increasing | Mosquitto + SQLite |
| Sensor simulator | python simulator/simulator.py --units 3 | — | Check MQTT topic has messages | Mosquitto |
| FastAPI ML backend | uvicorn api.main:app --host 0.0.0.0 --port 8000 | 8000 | curl localhost:8000/health | SQLite + models/saved/ |
| Streamlit dashboard | streamlit run dashboard/app.py --server.port 8501 | 8501 | Browser: localhost:8501 | FastAPI |

**Startup order**: Mosquitto → DB Writer → Simulator → FastAPI → Streamlit
**Startup time**: < 30 seconds from cold start
**Orchestration**: Single `start.sh` script with 3-second delays between services

### 13.2 Docker Compose Configuration

```yaml
version: '3.8'
services:
  mosquitto:
    image: eclipse-mosquitto:2.0
    ports: ['1883:1883']
    volumes: ['./config/mosquitto.conf:/mosquitto/config/mosquitto.conf']
  db_writer:
    build: ./simulator
    command: python mqtt_subscriber.py
    depends_on: [mosquitto]
    volumes: ['sqlite_data:/data']
  simulator:
    build: ./simulator
    command: python simulator.py --units 3 --speed 1.0
    depends_on: [mosquitto, db_writer]
  api:
    build: ./api
    ports: ['8000:8000']
    depends_on: [db_writer]
    volumes: ['sqlite_data:/data', 'model_files:/models']
  dashboard:
    build: ./dashboard
    ports: ['8501:8501']
    depends_on: [api]
volumes:
  sqlite_data:  # Shared: db_writer writes, api reads
  model_files:  # Shared: train writes .pkl/.pt, api loads
```

### 13.3 Production Deployment - Cloud Architecture

| Component | AWS Service | Alternatives | Scaling Strategy |
|-----------|-------------|--------------|-----------------|
| MQTT broker | AWS IoT Core (managed) | HiveMQ Cloud, Azure IoT Hub | Auto-scales to millions of messages/sec |
| Time-series storage | Amazon Timestream or InfluxDB on EC2 | TimescaleDB on RDS, ClickHouse | Partition by equipment_id + time; retention policy 2 years |
| ML inference API | FastAPI on ECS Fargate | Azure Container Instances | CPU-based auto-scaling 1-10 tasks based on request rate |
| Model training pipeline | AWS SageMaker Training Jobs | Azure ML, Google Vertex AI | Scheduled weekly; training on GPU spot instances |
| Model registry | SageMaker Model Registry | MLflow on EC2 | Version tracking, approval workflow, A/B deployment |
| Dashboard | Grafana on EC2 (or Streamlit Enterprise) | Power BI Embedded, Retool | Multi-user; LDAP/AD authentication |
| Secrets | AWS Secrets Manager | HashiCorp Vault | Rotate credentials without redeployment |
| CI/CD | GitHub Actions → ECR → ECS | Azure DevOps | Model validation gate before deploy |

---

## 14. Testing Strategy

### 14.1 Test Plan Overview

| Test Level | Scope | Tooling | Pass Threshold | When Run |
|-----------|-------|---------|----------------|----------|
| Unit (UT) | Individual functions: preprocessing, feature engineering, scheduler formula, data quality checks | pytest 8.0+ | 100% critical functions covered; 0 failures | Every code commit |
| Model Validation (MT) | ML model accuracy on held-out C-MAPSS test set | pytest + sklearn metrics + PyTorch evaluate | RMSE < 25, AUC > 0.80, F1 > 0.75 | Before each model deployment |
| API Integration (IT) | All 13 API endpoints return correct schema and HTTP status | pytest + httpx (async) | All endpoints 200 OK; response validates against JSON schema | Every API code change |
| End-to-End (E2E) | Simulator → MQTT → DB → ML → Dashboard shows correct alert | Manual test script (13 steps) | All steps pass; alert visible < 15s after failure event | Before every demo |
| Performance (PT) | API response time under 5 concurrent requests | locust or pytest-benchmark | p95 < 200ms; p99 < 500ms | Weekly or before major demo |
| Regression | Re-run full test suite after any change | pytest --all | 0 regressions from previously passing tests | Before every demo |

### 14.2 Model Validation Protocol

1. Split C-MAPSS data: 80% train / 20% validation — split by engine ID (not rows) to prevent leakage.
2. Train all models on training split. Save scaler parameters alongside model files.
3. Evaluate all models on validation split. Record all metrics in model_metadata table.
4. Run final evaluation on official C-MAPSS test files with ground-truth RUL_FD001.txt.
5. Compare against published benchmarks (target: competitive with top-10 C-MAPSS leaderboard results).
6. Run data quality unit tests: verify preprocessing produces correct shapes and value ranges.
7. Approve models only if all metrics exceed minimum thresholds in Section 16.1.

### 14.3 Demo Verification Script (13-Step)

Execute completely before any live presentation. Expected total runtime: 3 minutes.

| Step | Action | Expected Result | Timeout |
|------|--------|-----------------|---------| 
| 1 | Run start.sh; wait 30 seconds | All 5 services running; no error output | 60s |
| 2 | curl localhost:8000/health | { api:ok, db:ok, models:{all loaded} } | 5s |
| 3 | Check sensor_readings table | New rows appearing; timestamps within last 10s | 10s |
| 4 | Set EXC-01 simulator to phase=imminent_failure | Simulator switches lifecycle stage | 5s |
| 5 | Wait 15 seconds; check predictions table | anomaly_label=critical, failure_prob > 0.70 for EXC-01 | 20s |
| 6 | Check alerts table | Alert row with severity=critical for EXC-01 | 5s |
| 7 | Open localhost:8501 in browser | Dashboard loads; EXC-01 card shows RED badge | 10s |
| 8 | Observe dashboard auto-refresh | EXC-01 status updates to CRITICAL within 5s without manual reload | 10s |
| 9 | Click EXC-01 card | Equipment detail opens; vibration chart rising; SHAP shows top sensors | 5s |
| 10 | Navigate to Schedule screen | EXC-01 appears as rank-1 job with action text | 5s |
| 11 | Navigate to Alert Feed | EXC-01 critical alert shown at top with sensor attribution | 5s |
| 12 | Click Acknowledge on EXC-01 alert | Alert moves to Resolved section; audit record created | 5s |
| 13 | Reset EXC-01 to phase=healthy; wait 30s | EXC-01 returns to NORMAL status | 40s |

---

## 15. Implementation Plan

### 15.1 Technology Stack

| Layer | Technology | Version | License | Justification |
|-------|-----------|---------|---------|---------------|
| IoT simulation | Python paho-mqtt | 1.6+ | OSI Approved | Industry-standard MQTT client; async support |
| Message broker | Mosquitto | 2.0 | EPL | Lightweight, zero-config for local dev |
| Database (prototype) | SQLite + SQLAlchemy | 3.x + 2.0 | Public domain + MIT | Zero setup; sufficient for hackathon volumes |
| Database (production) | InfluxDB 3.0 / TimescaleDB | — | MIT/Apache | Purpose-built time-series; 10-100× faster queries |
| ML - anomaly | scikit-learn IsolationForest | 1.3+ | BSD | Mature; fast; SHAP compatible |
| ML - classifier | XGBoost | 2.0+ | Apache 2.0 | Best-in-class tabular; native SHAP support |
| ML - regression | PyTorch LSTM | 2.0+ | BSD | Flexible; production-ready; MPS support for Apple Silicon |
| Explainability | SHAP | 0.44+ | MIT | De facto standard; TreeExplainer 10× faster for XGBoost |
| API backend | FastAPI + Uvicorn | 0.110+ / 0.29+ | MIT | Auto OpenAPI docs; async; Pydantic validation |
| Job scheduler | APScheduler | 3.10+ | MIT | In-process; cron and interval triggers |
| Dashboard | Streamlit | 1.32+ | Apache 2.0 | Python-native; fastest path to interactive web UI |
| Charts | Plotly | 5.20+ | MIT | Interactive; gauges; Gantt; heatmaps |
| Testing | pytest + httpx | 8.0+ / 0.27+ | MIT | Industry standard; async API testing |
| Containerization | Docker + Docker Compose | 24+ / 2.24+ | Apache 2.0 | Reproducible environment |

### 15.2 Project Structure

```
predictive-maintenance/
├── config/
│   ├── mosquitto.conf                # MQTT broker config
│   └── equipment_profiles.json       # Sensor specs, thresholds, FMEA mapping
├── data/
│   ├── raw/                          # NASA C-MAPSS .txt files
│   ├── processed/                    # Normalized, feature-engineered .csv files
│   └── scalers/                      # Saved MinMaxScaler.pkl files
├── models/
│   ├── train/
│   │   ├── 01_preprocess.py          # Data loading, RUL labeling, feature engineering
│   │   ├── 02_train_anomaly.py       # Isolation Forest training + evaluation
│   │   ├── 03_train_failure.py       # XGBoost training + SHAP analysis
│   │   └── 04_train_rul.py           # LSTM training + evaluation
│   ├── saved/                        # anomaly_v1.pkl, xgb_failure_v1.pkl, lstm_rul_v1.pt
│   └── evaluate/
│       └── model_report.ipynb        # Evaluation notebook with charts
├── simulator/
│   ├── simulator.py                  # Sensor simulator + MQTT publisher
│   ├── mqtt_subscriber.py            # MQTT consumer + SQLite writer
│   └── equipment_profiles.py         # Lifecycle state machine per equipment type
├── api/
│   ├── main.py                       # FastAPI app + startup events
│   ├── routes/
│   │   ├── equipment.py              # /equipment endpoints
│   │   ├── alerts.py                 # /alerts endpoints
│   │   ├── schedule.py               # /schedule endpoints
│   │   ├── dashboard.py              # /dashboard/kpi + /dashboard/summary
│   │   ├── health.py                 # /health endpoint
│   │   ├── reports.py                # /reports/latest PDF generation
│   │   └── integrations.py           # /integrations/cmms/work-order stub
│   ├── services/
│   │   ├── inference_service.py      # Loads models, runs prediction pipeline
│   │   ├── scheduler_service.py      # Priority scoring + scheduling algorithm
│   │   ├── db_service.py             # SQLAlchemy session management
│   │   └── drift_service.py          # KS test drift detection
│   └── models/
│       ├── orm_models.py             # SQLAlchemy table definitions
│       └── schema.py                 # Pydantic request/response schemas
├── dashboard/
│   ├── app.py                        # Streamlit main entrypoint + navigation
│   ├── pages/
│   │   ├── fleet_overview.py         # Screen 1
│   │   ├── equipment_detail.py       # Screen 2
│   │   ├── kpi_dashboard.py          # Screen 3 (Plant Manager)
│   │   ├── schedule.py               # Screen 4
│   │   └── alert_feed.py             # Screen 5
│   └── components/
│       ├── gauge.py                  # Reusable RUL gauge component
│       ├── sensor_chart.py           # Reusable sensor trend chart
│       ├── shap_chart.py             # SHAP attribution horizontal bar
│       └── alert_card.py             # Alert card with acknowledge button
├── tests/
│   ├── test_preprocessing.py         # Unit tests for feature engineering
│   ├── test_scheduler.py             # Unit tests for priority scoring formula
│   ├── test_api.py                   # Integration tests for all endpoints
│   └── test_data_quality.py          # Unit tests for quality flag logic
├── reports/                          # Generated DGMS compliance reports
├── notebooks/
│   ├── eda.ipynb                     # Exploratory data analysis on C-MAPSS
│   └── model_comparison.ipynb        # Algorithm comparison study
├── docker-compose.yml
├── requirements.txt                  # All Python dependencies with pinned versions
├── start.sh                          # One-command system startup
└── README.md                         # Judge setup guide: < 5 minutes to running
```

### 15.3 Build Sequence with Team Allocation

| Step | Task | Owner | Time | Completion Check |
|------|------|-------|------|-----------------|
| 1 | Download + explore C-MAPSS; write preprocessing script; verify shapes | ML Engineer | 2 hrs | X_train.shape=(N,56), y_train.shape=(N,) |
| 2 | Train Isolation Forest; tune thresholds; evaluate F1 | ML Engineer | 1.5 hrs | F1 > 0.70 on validation |
| 3 | Train XGBoost; tune scale_pos_weight; evaluate AUC | ML Engineer | 2 hrs | AUC > 0.75 on validation |
| 4 | Build FastAPI skeleton + SQLAlchemy schema + /health | Backend | 1 hr | GET /health returns 200 |
| 5 | Configure Mosquitto; write MQTT subscriber with quality checks | Backend | 1 hr | Rows appear in sensor_readings within 30s of test publish |
| 6 | Write simulator with lifecycle state machine (3 equipment units) | Backend | 2 hrs | 3 units publishing at 1 Hz; EXC-01 triggers critical in 3 min |
| 7 | Connect ML models to FastAPI inference service + APScheduler | Backend + ML | 2 hrs | GET /equipment returns model predictions |
| 8 | Train LSTM RUL model (use Colab if needed); add to API | ML Engineer | 4 hrs | RMSE < 30 on FD001 test set; GET /equipment/{id}/rul works |
| 9 | Build Streamlit: fleet overview + equipment detail + sensor charts | Frontend | 3 hrs | Red badge fires on simulated failure within 5s |
| 10 | Add SHAP integration + alert feed screen + acknowledge flow | Frontend + ML | 2 hrs | Alert shows top-3 sensors; acknowledge moves to resolved |
| 11 | Build schedule screen + KPI dashboard screen + export buttons | Frontend | 2 hrs | Schedule ranks EXC-01 first; CSV download works |
| 12 | Add data quality alerts + drift detection logging + DGMS report | Backend | 1.5 hrs | quality_flag=suspect on out-of-range reading; PDF report generated |
| 13 | Run 13-step demo script; fix issues; record screen capture backup | All | 2 hrs | All 13 steps pass; backup video saved |
| 14 | Write README setup guide; architecture diagram for presentation | All | 1 hr | Judge can run from README in < 5 minutes |

---

## 16. Evaluation, Benchmarks & Future Roadmap

### 16.1 Success Metrics

| Model/System | Metric | Minimum Target | Stretch Target | How Measured |
|--------------|--------|----------------|----------------|--------------| 
| Anomaly Detector | F1-score | 0.75 | 0.87 | C-MAPSS validation set |
| Anomaly Detector | False Positive Rate | < 5% | < 2% | Healthy period false alarms / total predictions |
| Failure Predictor | AUC-ROC | 0.80 | 0.91 | sklearn.metrics.roc_auc_score on validation set |
| Failure Predictor | AUC-PR | 0.72 | 0.85 | More informative for imbalanced class |
| RUL Estimator | RMSE (cycles) | < 25 | < 15 | sqrt(mean_squared_error) on C-MAPSS test set |
| RUL Estimator | NASA Asymmetric Score | < 400 | < 250 | Per NASA scoring function |
| API | p95 response time | < 200ms | < 80ms | locust load test: 5 concurrent users |
| Dashboard | Alert display after failure event | < 10s | < 5s | Stopwatch from simulator failure trigger to red badge |
| Scheduler | Critical equipment ranked first | 100% | 100% | Manual verification in 13-step demo script |
| Demo script | Steps passing | 13/13 | 13/13 + live Q&A | 13-step verification script |

### 16.2 Benchmark Comparison — State of the Art

| Approach | RMSE (FD001) | AUC (Failure Pred) | Explainability | Real-Time Capable |
|----------|--------------|--------------------|----------------|-------------------|
| Simple RUL linear baseline | ~46 cycles | N/A | Yes (linear) | Yes |
| Random Forest (tabular features) | ~29 cycles | ~0.81 | Partial (feature importance) | Yes |
| LSTM (standard, no asymmetric loss) | ~18 cycles | N/A | No | Yes (slow) |
| CNN-LSTM (literature SOTA) | ~13 cycles | N/A | No | Limited |
| Transformer (BERT for time-series) | ~12 cycles | ~0.93 | No | No (too slow) |
| **AIPMS (XGBoost + LSTM + IF)** | **< 20 cycles (target)** | **~0.87 (target)** | **Yes (SHAP)** | **Yes (< 100ms)** |

AIPMS prioritizes the explainability + real-time combination that literature SOTA models sacrifice for marginal accuracy gains. An explainable 80% accurate prediction that engineers trust is more valuable than a 95% accurate black box they ignore.

### 16.3 Judging Criteria Alignment

| PS-1 Requirement | AIPMS Deliverable | Quality Assessment |
|-----------------|-------------------|-------------------|
| IoT data integration | MQTT simulator + subscriber + 5-layer architecture + production HW BOM | Exceeds: bridges prototype to production clearly with hardware specifications |
| Anomaly detection | Isolation Forest with SHAP; 3-level classification; data quality guards | Exceeds: explains WHY anomaly occurred, not just THAT it occurred |
| Failure prediction | XGBoost with 7-day horizon; calibrated probability; FMEA failure mode mapping | Exceeds: links prediction to specific failure mode from engineering FMEA |
| RUL estimation | LSTM with asymmetric loss; confidence intervals; 30-day trend history | Exceeds: uncertainty quantification via bootstrap ensemble CI |
| Dashboard / interface | 5-screen Streamlit: fleet overview, equipment detail, KPI (manager), schedule, alerts | Exceeds: different screens for different personas; plant manager KPI view |
| Scheduling optimization | Priority formula with cost-minimization math; constraint model; CMMS integration | Exceeds: formal optimization problem statement; escalation workflow documented |
| Working prototype | 13-step demo script; Docker Compose; start.sh; judge README | Exceeds: reproducible in < 5 minutes on any laptop |
| System design | This document; architecture diagrams; network topology; IoT BOM | Exceeds: 16 sections covering every aspect of the problem space |

### 16.4 Risk Register

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| LSTM training > 4 hours on CPU | Medium | High | Train on Google Colab (free T4 GPU); or use XGBoost regressor as M3 fallback (trains in < 60s, RMSE ~28 cycles) |
| XGBoost AUC < 0.75 on first run | Low | Medium | Add polynomial interaction features; tune scale_pos_weight more aggressively; try LightGBM as drop-in replacement |
| MQTT broker configuration fails | Low | High | Fallback: replace MQTT with direct HTTP POST from simulator to FastAPI; 20-minute code swap; no dashboard change needed |
| Live demo laptop performance issue | Medium | High | All computation is local — no internet needed; pre-test exactly on demo hardware 24 hours prior; keep screen recording as backup |
| Streamlit refresh too slow | Low | Medium | Use st.empty() selective updates instead of full page rerun; pre-aggregate data server-side in /dashboard/summary endpoint |
| SHAP library import error | Low | Medium | Fallback: use XGBoost built-in model.get_score(importance_type='gain') — available without SHAP installation |
| C-MAPSS accuracy insufficient | Low | Low | Address proactively in presentation: acknowledge domain shift from turbofans to mining; show architecture is ready for real mining data |
| Team member unavailable day-of | Low | High | All team members can independently run the full demo; shared run-book in README; no single point of knowledge |
| Data leakage in ML pipeline | Low | High | Split by engine_id (not rows) for train/val; verified in test_preprocessing.py unit test before training |

### 16.5 Future Roadmap

| Phase | Timeline | Objective | Key Milestones |
|-------|----------|-----------|----------------|
| Phase 1 — Real Data | Month 1–3 | Partner with BCCL or ECL for pilot deployment on 3 machines | Install IoT BOM; collect 90 days labeled data; retrain models on mining data |
| Phase 2 — Production Hardening | Month 3–6 | Production-grade system on cloud with real equipment | AWS IoT Core + InfluxDB + ECS; TLS security; SAP PM integration; SLA monitoring |
| Phase 3 — Mobile App | Month 4–7 | Field technician mobile access | React Native app: job details, parts list, work order photo upload, offline mode |
| Phase 4 — Fleet Expansion | Month 6–12 | Scale to full mine fleet (30–50 machines) | Multi-mine federation; centralized model training; fleet-level analytics |
| Phase 5 — Advanced AI | Month 9–18 | Next-generation predictive capabilities | Federated learning across mine sites; digital twin simulation; RL-based maintenance scheduling; speech alerts for technicians |

---

## 17. CMMS & ERP Integration

### 17.1 SAP PM Integration

| Integration Point | Data Direction | SAP PM Object | Trigger | Status |
|------------------|----------------|---------------|---------|--------|
| Critical alert → Work Order | AIPMS → SAP PM | PM01 Work Order | Priority_Score > 0.75 AND alert unacknowledged > 2 hrs | Stub implemented |
| Work Order completion → AIPMS | SAP PM → AIPMS | PM02 Work Order completion notification | Technician marks complete in SAP PM | Webhook endpoint |
| Spare parts availability | AIPMS → SAP PM query | Material Management (MM) stock | Before scheduling job: check if parts in stock | Read-only API call |
| Equipment master data sync | SAP PM → AIPMS | Equipment Master (IE03) | Daily sync: commissioned date, operating hours | Nightly batch import |

### 17.2 Work Order API Payload Example

```json
{
  "equipment_id": "EXC-01",
  "equipment_sap_id": "10001234",
  "work_order_type": "PM01",
  "priority": "1-Very High",
  "failure_mode": "FM-06: Hydraulic pump cavitation / seal wear",
  "recommended_action": "Inspect hydraulic pump seals; replace if flow rate < 85% nominal",
  "failure_probability": 0.78,
  "rul_hours": 31.5,
  "scheduled_window_start": "2025-04-16T04:30:00+05:30",
  "estimated_duration_hours": 4.0,
  "parts_required": [
    {"material_number": "PM-HYD-SEAL-01", "quantity": 1, "description": "Hydraulic pump seal kit"},
    {"material_number": "PM-HYD-FILTER-02", "quantity": 2, "description": "Hydraulic oil filter"}
  ],
  "aipms_alert_id": 42,
  "created_by": "AIPMS_SYSTEM"
}
```

---

## Appendix A — Complete Dependencies

| Package | Version | Install | Purpose |
|---------|---------|---------|---------|
| pandas | >=2.0 | pip install pandas | Data manipulation, feature engineering |
| numpy | >=1.24 | pip install numpy | Numerical operations, array math |
| scikit-learn | >=1.3 | pip install scikit-learn | Isolation Forest, MinMaxScaler, metrics |
| xgboost | >=2.0 | pip install xgboost | Failure prediction classifier |
| torch | >=2.0 | pip install torch | LSTM neural network |
| shap | >=0.44 | pip install shap | SHAP explainability for XGBoost |
| fastapi | >=0.110 | pip install fastapi | REST API framework |
| uvicorn | >=0.29 | pip install uvicorn[standard] | ASGI server |
| apscheduler | >=3.10 | pip install apscheduler | Background inference + scheduler jobs |
| sqlalchemy | >=2.0 | pip install sqlalchemy | SQLite ORM |
| paho-mqtt | >=1.6 | pip install paho-mqtt | MQTT client |
| streamlit | >=1.32 | pip install streamlit | Dashboard UI |
| plotly | >=5.20 | pip install plotly | Interactive charts, gauges, Gantt |
| requests | >=2.31 | pip install requests | HTTP client for Streamlit → FastAPI |
| scipy | >=1.11 | pip install scipy | KS test for drift detection |
| reportlab | >=4.0 | pip install reportlab | DGMS PDF report generation |
| pytest | >=8.0 | pip install pytest | Unit + integration testing |
| httpx | >=0.27 | pip install httpx | Async HTTP client for API tests |
| python-dotenv | >=1.0 | pip install python-dotenv | Environment variable management |

---

## Appendix B — Dataset Download

- **NASA C-MAPSS**: https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6
- **Kaggle mirror** (easier): https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
- **Required files**: train_FD001.txt, test_FD001.txt, RUL_FD001.txt
- **Column format**: engine_id, cycle, op_setting_1, op_setting_2, op_setting_3, sensor_1 ... sensor_21 (space-separated, no header)
- **Optional**: FD002, FD003, FD004 for multi-condition training

---

## Appendix C — Glossary

| Term | Definition |
|------|-----------|
| AIPMS | AI-driven Predictive Maintenance System — this project |
| RUL | Remaining Useful Life — estimated operational time before component failure |
| FMEA | Failure Mode and Effects Analysis — systematic identification of failure modes, causes, effects |
| MTBF | Mean Time Between Failures — average time between successive equipment failures |
| C-MAPSS | Commercial Modular Aero-Propulsion System Simulation — NASA turbofan degradation dataset |
| Isolation Forest | Unsupervised ML anomaly detection via random recursive data partitioning |
| XGBoost | Extreme Gradient Boosting — sequential ensemble of gradient-boosted decision trees |
| LSTM | Long Short-Term Memory — RNN with input/forget/output gates for temporal sequence modeling |
| SHAP | SHapley Additive exPlanations — game-theory-based per-prediction feature attribution method |
| AUC-ROC | Area Under ROC Curve — classifier performance metric across all decision thresholds |
| AUC-PR | Area Under Precision-Recall Curve — more informative than ROC for imbalanced classes |
| NASA Score | Asymmetric evaluation metric for RUL: late predictions penalized 3× more than early predictions |
| MQTT | Message Queuing Telemetry Transport — ISO/IEC 20922 lightweight pub/sub IoT protocol |
| QoS | Quality of Service — MQTT delivery guarantee levels: 0 (fire-and-forget), 1 (at-least-once), 2 (exactly-once) |
| CMMS | Computerized Maintenance Management System — SAP PM, IBM Maximo |
| DGMS | Directorate General of Mines Safety — Indian regulatory authority for mine safety |
| APScheduler | Advanced Python Scheduler — in-process cron/interval job scheduling library |
| Bootstrap Ensemble | ML technique: train N models with different random seeds; use output distribution for confidence intervals |
| Concept Drift | Change in statistical relationship between input features and target variable over time |
| Feature Drift | Change in statistical distribution of input features over time (distinct from concept drift) |
| PII | Personally Identifiable Information — privacy-sensitive personal data |
| BCCL | Bharat Coking Coal Limited — Major coal company in Dhanbad |
| BOM | Bill of Materials — Component list for hardware procurement |
| CI/CD | Continuous Integration / Continuous Deployment — Software delivery pipeline |
| TLS | Transport Layer Security — Encryption protocol |
| JWT | JSON Web Token — Authentication token format |
| SSO | Single Sign-On — Centralized authentication |
| MTTR | Mean Time To Repair — Maintenance efficiency metric |

---

## Appendix D — References

- Saxena, A. et al. (2008). Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation. NASA Ames Research Center. — C-MAPSS dataset source
- Liu, R. et al. (2019). Remaining Useful Life Estimation under Uncertainty with Causal GraphNets. arXiv:1905.04905
- Chen, T. & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. KDD 2016
- Liu, F.T., Ting, K.M., Zhou, Z. (2008). Isolation Forest. IEEE ICDM 2008
- Lundberg, S. & Lee, S. (2017). A Unified Approach to Interpreting Model Predictions (SHAP). NeurIPS 2017
- DGMS Circular No. 8 of 2018 — Condition Monitoring of Major Mining Equipment
- Coal Mines Regulations 2017. Ministry of Labour & Employment, Government of India
- ISO 13381-1:2015 — Condition monitoring and diagnostics of machines
- ISO 17359:2018 — Condition monitoring and diagnostics of machine systems. General guidelines
- NASA Prognostics Center of Excellence Data Repository

---

**Document Version**: v3.0 — Final
**Prepared By**: Team AIPMS
**Date**: April 2025
**Status**: FINAL — Ready for Submission

---

*End of Document | AI-Driven Predictive Maintenance System | PS-1 | BIT Sindri Hackathon 2025*
