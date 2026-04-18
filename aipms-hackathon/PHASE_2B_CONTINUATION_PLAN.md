# Phase 2B Continuation Plan - Dataset Integration & Model Training Setup

**Objective:** Implement dataset integration, train/test splitting, cross-validation, model training infrastructure, and performance tracking for AIPMS predictive maintenance system.

**Current State:** 
- ✅ PreprocessingPipeline complete with 16/16 tests passing
- ✅ Feature engineering producing (n, 68) feature vectors
- ⏳ Ready for real data integration and model training

**Target State:**
- Dataset integration (NASA C-MAPSS or synthetic)
- Train/test temporal split preserving time-series integrity
- K-fold cross-validation infrastructure
- Model training framework for Isolation Forest, XGBoost, LSTM
- Performance metrics and evaluation tracking

---

## Dependency Graph

```
Step 1: Dataset Manager Implementation
    ↓
Step 2: Train/Test Split Implementation
    ↓
Step 3: Cross-Validation Framework
    ↓
Step 4 (parallel): Anomaly Detection Model Training
Step 5 (parallel): Failure Prediction Model Training
Step 6 (parallel): RUL Regression Model Training
    ↓
Step 7: Performance Metrics & Evaluation
    ↓
Step 8: Integration Tests & Demo
```

**Parallelizable:** Steps 4, 5, 6 can run independently after Step 3
**Critical Path:** 1 → 2 → 3 → (4|5|6) → 7 → 8

---

## Step 1: Dataset Manager Implementation

**Objective:** Create unified data loader supporting both synthetic and real NASA C-MAPSS datasets.

**Context Brief:**
- Create `models/train/data_manager.py` with DatasetManager class
- Support FD001-FD004 C-MAPSS subsets
- Fallback to synthetic data for local testing
- Handle data validation and caching

**Tasks:**
- [ ] Create DatasetManager class with dataset registry
- [ ] Implement download_cmapss() for automatic dataset fetch
- [ ] Add synthetic_dataset() for local testing
- [ ] Implement data validation (shape, type, value checks)
- [ ] Add caching layer to avoid re-downloading

**Code Location:** `models/train/data_manager.py`

**Test Location:** `tests/test_data_manager.py`

**Success Criteria:**
```python
# Should work with real data
dm = DatasetManager()
X, y = dm.load('FD001')
assert X.shape == (20631, 17)
assert y.shape == (20631,)

# Should work with synthetic data
X_syn, y_syn = dm.synthetic_dataset(n_engines=5)
assert X_syn.shape[1] == 17
```

**Verification Command:**
```bash
python -m pytest tests/test_data_manager.py -v
```

**Rollback:** Delete `models/train/data_manager.py` and `tests/test_data_manager.py`

---

## Step 2: Train/Test Split Implementation

**Objective:** Implement temporal split respecting time-series structure and preventing data leakage.

**Context Brief:**
- Create `models/train/split_strategy.py` with temporal split logic
- Split by engine ID (keep entire engines in same fold)
- Ensure train data all cycles before test cycles
- No future information leakage

**Tasks:**
- [ ] Implement TemporalSplit class for train/test separation
- [ ] Add engine-aware splitting (don't mix engines in fold)
- [ ] Implement cycle-boundary enforcement (no cycle overlap)
- [ ] Add cycle-count minimum requirements
- [ ] Create visualizations of split distribution

**Code Location:** `models/train/split_strategy.py`

**Test Location:** `tests/test_split_strategy.py`

**Success Criteria:**
```python
# Temporal split: all train cycles < test cycles
split = TemporalSplit(test_ratio=0.2)
train_idx, test_idx = split.split(X, y, engine_ids)

train_max_cycle = data.loc[train_idx, 'cycle'].max()
test_min_cycle = data.loc[test_idx, 'cycle'].min()
assert train_max_cycle < test_min_cycle  # No overlap

# Engine-aware: no engine in both train and test
train_engines = set(engine_ids[train_idx])
test_engines = set(engine_ids[test_idx])
assert len(train_engines & test_engines) == 0
```

**Verification Command:**
```bash
python -m pytest tests/test_split_strategy.py -v
```

**Rollback:** Delete `models/train/split_strategy.py` and `tests/test_split_strategy.py`

---

## Step 3: Cross-Validation Framework

**Objective:** Implement k-fold cross-validation respecting time-series structure.

**Context Brief:**
- Create `models/train/cross_validation.py` with TimeSeriesFold class
- Implement walk-forward validation (train on past, test on future)
- Add stratified splitting on RUL distribution
- Support k-fold for hyperparameter tuning

**Tasks:**
- [ ] Implement TimeSeriesFold (walk-forward) class
- [ ] Add RUL stratification (ensure similar RUL dist in each fold)
- [ ] Implement KFold wrapper for compatibility
- [ ] Add fold visualization and metrics tracking
- [ ] Create cv_split_indices helper function

**Code Location:** `models/train/cross_validation.py`

**Test Location:** `tests/test_cross_validation.py`

**Success Criteria:**
```python
# Walk-forward validation
cv = TimeSeriesFold(n_splits=5)
folds = list(cv.split(X, y, engine_ids))
assert len(folds) == 5

# Verify train < test cycle ranges
for train_idx, test_idx in folds:
    assert data.loc[train_idx, 'cycle'].max() < data.loc[test_idx, 'cycle'].min()
```

**Verification Command:**
```bash
python -m pytest tests/test_cross_validation.py -v
```

**Rollback:** Delete `models/train/cross_validation.py` and `tests/test_cross_validation.py`

---

## Step 4: Anomaly Detection Model Training (Isolation Forest)

**Objective:** Train and evaluate Isolation Forest for anomaly detection on preprocessed data.

**Context Brief:**
- Create `models/train/train_anomaly_model.py` with AnomalyDetectorTrainer
- Use cross-validation from Step 3
- Tune hyperparameters: contamination, n_estimators, max_samples
- Track performance: F1, Precision, Recall, ROC-AUC
- Save best model to `models/saved/anomaly_detector_v1.pkl`

**Tasks:**
- [ ] Create AnomalyDetectorTrainer with fit() and evaluate() methods
- [ ] Implement hyperparameter grid search
- [ ] Add cross-validation loop with fold averaging
- [ ] Implement performance metrics calculation
- [ ] Add model persistence and versioning
- [ ] Create training logs and model metadata

**Code Location:** `models/train/train_anomaly_model.py`

**Test Location:** `tests/test_train_anomaly_model.py`

**Success Criteria:**
```python
trainer = AnomalyDetectorTrainer(contamination=0.05)
results = trainer.train_with_cv(X, y, cv=TimeSeriesFold(n_splits=5))

assert results['mean_f1'] > 0.70
assert results['mean_auc'] > 0.75
assert Path('models/saved/anomaly_detector_v1.pkl').exists()
```

**Verification Command:**
```bash
python -m pytest tests/test_train_anomaly_model.py -v
python models/train/train_anomaly_model.py --verbose
```

**Rollback:** Delete `models/train/train_anomaly_model.py`, tests, and trained model file

---

## Step 5: Failure Prediction Model Training (XGBoost)

**Objective:** Train XGBoost classifier for 7-day failure prediction with calibration.

**Context Brief:**
- Create `models/train/train_failure_model.py` with FailurePredictorTrainer
- Handle class imbalance via scale_pos_weight
- Implement early stopping on validation set
- Add Platt scaling for probability calibration
- SHAP feature importance tracking
- Save model to `models/saved/failure_predictor_v1.pkl`

**Tasks:**
- [ ] Create FailurePredictorTrainer with fit() and evaluate()
- [ ] Implement hyperparameter optimization (n_estimators, max_depth, learning_rate)
- [ ] Add early stopping callback (AUC-based)
- [ ] Implement probability calibration (Platt scaling)
- [ ] Add SHAP importance computation
- [ ] Track cross-validation metrics by fold
- [ ] Generate feature importance plots

**Code Location:** `models/train/train_failure_model.py`

**Test Location:** `tests/test_train_failure_model.py`

**Success Criteria:**
```python
trainer = FailurePredictorTrainer(scale_pos_weight=3.5)
results = trainer.train_with_cv(X, y, cv=TimeSeriesFold(n_splits=5))

assert results['mean_auc_roc'] > 0.80
assert results['mean_auc_pr'] > 0.70
assert Path('models/saved/failure_predictor_v1.pkl').exists()
assert 'shap_importances' in results
```

**Verification Command:**
```bash
python -m pytest tests/test_train_failure_model.py -v
python models/train/train_failure_model.py --verbose
```

**Rollback:** Delete trainer, tests, and model files

---

## Step 6: RUL Regression Model Training (LSTM)

**Objective:** Train LSTM neural network for Remaining Useful Life regression with confidence intervals.

**Context Brief:**
- Create `models/train/train_rul_model.py` with RULEstimatorTrainer
- Network: 2-layer LSTM with dropout and dense layers
- Loss: Asymmetric MSE (overestimates penalized 1.5×)
- Output: RUL point estimate + 95% confidence interval
- Bootstrap ensemble for CI computation
- Save to `models/saved/rul_estimator_v1.pt`

**Tasks:**
- [ ] Create LSTM network architecture (50 hidden, 32 hidden, 16 dense)
- [ ] Implement asymmetric loss function
- [ ] Add learning rate scheduling
- [ ] Implement early stopping on validation RMSE
- [ ] Create bootstrap ensemble trainer (10 models)
- [ ] Add confidence interval computation
- [ ] Track metrics: RMSE, MAE, R², NASA Score

**Code Location:** `models/train/train_rul_model.py`

**Test Location:** `tests/test_train_rul_model.py`

**Success Criteria:**
```python
trainer = RULEstimatorTrainer(n_epochs=100, batch_size=256)
results = trainer.train_with_cv(X_seq, y_rul, cv=TimeSeriesFold(n_splits=5))

assert results['mean_rmse'] < 25  # cycles
assert results['mean_nasa_score'] < 400
assert Path('models/saved/rul_estimator_v1.pt').exists()
assert 'ci_95' in results
```

**Verification Command:**
```bash
python -m pytest tests/test_train_rul_model.py -v
python models/train/train_rul_model.py --verbose
```

**Rollback:** Delete trainer, tests, model files, and bootstrap ensemble

---

## Step 7: Performance Metrics & Evaluation

**Objective:** Create unified evaluation framework and model comparison dashboard.

**Context Brief:**
- Create `models/train/evaluate.py` with ModelEvaluator class
- Compute standard metrics for all 3 models
- Generate comparison tables and plots
- Create model cards with metadata
- Log all results to database for tracking
- Generate DGMS-compliance report template

**Tasks:**
- [ ] Create ModelEvaluator with evaluate_all_models() method
- [ ] Implement metric computation for each model type
- [ ] Create comparison tables (markdown, CSV)
- [ ] Generate performance plots (ROC, PR, feature importance, RUL scatter)
- [ ] Implement model card generation
- [ ] Add results persistence to SQLite
- [ ] Create DGMS compliance report template

**Code Location:** `models/train/evaluate.py`

**Test Location:** `tests/test_evaluate.py`

**Success Criteria:**
```python
evaluator = ModelEvaluator(test_set=(X_test, y_test, engine_ids_test))
results = evaluator.evaluate_all_models(
    anomaly_model=iso_forest,
    failure_model=xgb_model,
    rul_model=lstm_model
)

assert 'anomaly_detector' in results
assert 'failure_predictor' in results
assert 'rul_estimator' in results
assert results['anomaly_detector']['f1'] > 0.70
assert all(Path(f) for f in results['plots'].values())
```

**Verification Command:**
```bash
python -m pytest tests/test_evaluate.py -v
python models/train/evaluate.py --all-models
```

**Rollback:** Delete evaluator, tests, and results files

---

## Step 8: Integration Tests & Demo

**Objective:** End-to-end integration test and working demonstration.

**Context Brief:**
- Create `tests/test_integration_end_to_end.py` with full pipeline test
- Load → Preprocess → Split → Train → Evaluate
- Verify all models work with real shapes
- Create demo script with sample predictions
- Generate notebook for judges

**Tasks:**
- [ ] Create end-to-end integration test
- [ ] Implement demo prediction script
- [ ] Create Jupyter notebook walkthrough
- [ ] Add performance profiling (timing per stage)
- [ ] Generate final verification report
- [ ] Update README with Phase 2B results

**Code Location:** `tests/test_integration_end_to_end.py` + `demo_phase_2b_complete.py`

**Test Location:** Integration test in tests/ directory

**Success Criteria:**
```python
# Full pipeline works end-to-end
def test_complete_pipeline():
    # Data: Load
    dm = DatasetManager()
    X, y = dm.load('FD001')
    
    # Preprocess
    pipeline = PreprocessingPipeline()
    X_norm = pipeline.normalize_features(X)
    X_eng = pipeline.engineer_features(X_norm)
    
    # Split
    split = TemporalSplit()
    train_idx, test_idx = split.split(X_eng, y, engine_ids)
    
    # Train
    anomaly_trainer = AnomalyDetectorTrainer()
    anomaly_model = anomaly_trainer.train(X_eng[train_idx], y[train_idx])
    
    # Evaluate
    evaluator = ModelEvaluator((X_eng[test_idx], y[test_idx]))
    results = evaluator.evaluate_anomaly(anomaly_model)
    
    assert results['f1'] > 0.70
```

**Verification Command:**
```bash
python -m pytest tests/test_integration_end_to_end.py -v
python demo_phase_2b_complete.py
```

**Rollback:** Delete integration test and demo files

---

## Execution Order & Parallelization

### Sequential (Blocking Dependencies)
1. Step 1: Dataset Manager → **Required for all downstream**
2. Step 2: Train/Test Split → **Required for all training**
3. Step 3: Cross-Validation → **Required for all training**

### Parallel (After Step 3)
4. Step 4, 5, 6 can run in parallel:
   - Step 4: Anomaly Detection (Isolation Forest)
   - Step 5: Failure Prediction (XGBoost)
   - Step 6: RUL Regression (LSTM)

### Sequential (Final)
7. Step 7: Evaluation → **Requires all 3 trained models**
8. Step 8: Integration → **Requires evaluation complete**

**Estimated Parallelization Gain:** 40% time reduction if Steps 4-6 run in parallel

---

## File Structure Created

```
models/train/
├── preprocess.py                 # ✅ Existing
├── data_manager.py               # Step 1 - NEW
├── split_strategy.py             # Step 2 - NEW
├── cross_validation.py           # Step 3 - NEW
├── train_anomaly_model.py        # Step 4 - NEW
├── train_failure_model.py        # Step 5 - NEW
├── train_rul_model.py            # Step 6 - NEW
└── evaluate.py                   # Step 7 - NEW

tests/
├── test_preprocessing.py         # ✅ Existing (16/16 passing)
├── test_data_manager.py          # Step 1 - NEW
├── test_split_strategy.py        # Step 2 - NEW
├── test_cross_validation.py      # Step 3 - NEW
├── test_train_anomaly_model.py   # Step 4 - NEW
├── test_train_failure_model.py   # Step 5 - NEW
├── test_train_rul_model.py       # Step 6 - NEW
├── test_evaluate.py              # Step 7 - NEW
└── test_integration_end_to_end.py # Step 8 - NEW

models/saved/
├── anomaly_detector_v1.pkl       # Step 4 output
├── failure_predictor_v1.pkl      # Step 5 output
├── rul_estimator_v1.pt           # Step 6 output
└── model_metadata.json           # Model registry
```

---

## Critical Implementation Notes

### Dataset Handling
- **Real Data:** Download from NASA or use Kaggle mirror
- **Synthetic Data:** Generate for rapid iteration (3 engines, 100 cycles each)
- **Validation:** Check shapes (20631, 17) for real FD001

### Train/Test Split
- **Temporal:** Train cycles < test cycles per engine
- **Engine-Aware:** Keep engines separate (no cross-contamination)
- **Ratio:** Default 70/30 or engine-aware split for small fleets

### Cross-Validation
- **Walk-Forward:** Simulates real deployment (train on past, test on future)
- **Time Ordering:** Enforce cycle boundaries
- **Stratification:** On RUL distribution percentiles

### Model Training
- **Anomaly:** IF (Isolation Forest) - fast baseline, no tuning needed
- **Failure:** XGBoost - requires class weight tuning, early stopping
- **RUL:** LSTM - requires sequence preprocessing, bootstrap ensemble for CI

### Performance Tracking
- **Metrics DB:** SQLite table for all fold results
- **Artifact Storage:** Save models + metadata per version
- **Reporting:** Auto-generate markdown tables + plots

---

## Success Criteria Summary

| Step | Pass Threshold | Key Metric |
|------|---|---|
| 1 | Dataset loads without error | X.shape == (N, 17) |
| 2 | No data leakage, proper splitting | train_max_cycle < test_min_cycle |
| 3 | Valid CV splits, proper fold count | n_folds == k |
| 4 | Anomaly model achieves baseline | F1 > 0.70, AUC > 0.75 |
| 5 | Failure model outperforms baseline | AUC-ROC > 0.80, AUC-PR > 0.70 |
| 6 | RUL model regression acceptable | RMSE < 25 cycles, NASA Score < 400 |
| 7 | All metrics logged and visualized | Comparison plots generated |
| 8 | End-to-end pipeline functional | All 3 models work together |

---

## Rollback Strategy

Each step is independently rollbackable:
- **Code Rollback:** Delete step files and revert to previous commit
- **Data Rollback:** Delete trained models from `models/saved/`
- **Database Rollback:** Clear results table and re-run evaluation
- **Branch Rollback:** Revert to main, delete step branch

No cumulative risk — earlier steps don't depend on later ones for rollback.

---

## Next Actions

**Start with Step 1:** Implement DatasetManager
- Create `models/train/data_manager.py`
- Create `tests/test_data_manager.py`
- Verify with synthetic dataset first
- Implement real data download (optional for MVP)

**Proceed to Step 2:** Once Step 1 passes all tests
- Implement TemporalSplit
- Verify no data leakage
- Create visualization of split distributions

**Proceed to Steps 3–6:** Following dependency graph
- Cross-validation framework
- Three model trainers in parallel (Steps 4–6)
- Evaluation and integration (Steps 7–8)

---

**Estimated Total Time:**
- Step 1: 2 hours
- Step 2: 1.5 hours
- Step 3: 1.5 hours
- Steps 4–6 (parallel): 6 hours
- Step 7: 1 hour
- Step 8: 1 hour

**Total (sequential):** ~13 hours
**Total (with parallelization):** ~10 hours
