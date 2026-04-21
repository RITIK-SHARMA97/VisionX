"""
Phase 2B.4: Train Failure Prediction Model (XGBoost)
Predicts equipment failure within 7-day horizon using supervised learning

Model: XGBoost gradient boosted trees
Input: data/processed/FD001_X.npy, FD001_y.npy
Output: models/saved/failure_predictor_v1.pkl

Algorithm: XGBoost builds sequential decision trees. Each tree learns residuals
from previous trees. Handles imbalanced classes via scale_pos_weight.
"""

import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, roc_curve
import pickle
import os
import logging
import config_constants as cfg

logging.basicConfig(level=cfg.LOG_LEVEL, format=cfg.LOG_FORMAT)
logger = logging.getLogger(__name__)

# Try to import shap, but don't fail if it's unavailable due to memory constraints
try:
    import shap
    HAS_SHAP = True
except (ImportError, OSError):
    HAS_SHAP = False
    print("WARNING: SHAP not available (memory constraint), skipping explainability")

os.makedirs('models/saved', exist_ok=True)

print("=" * 80)
print("Phase 2B.4: Training Failure Prediction Model (XGBoost)")
print("=" * 80)

# Load training data
print("\n1. Loading training data...")
try:
    X_train_all = np.load('data/processed/FD001_X.npy')
    y_train_all = np.load('data/processed/FD001_y.npy')
    print(f"   [OK] Loaded training data: X={X_train_all.shape}, y={y_train_all.shape}")
except FileNotFoundError as e:
    print(f"   [ERROR] Missing data: {e}")
    print("   Run: python models/train/01_preprocess.py")
    exit(1)

# Train-validation split (80-20)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_all, y_train_all,
    test_size=0.2,
    random_state=42,
    stratify=y_train_all
)

print(f"   Train set: {X_train.shape}, Class distribution: {np.bincount(y_train)}")
print(f"   Val set: {X_val.shape}, Class distribution: {np.bincount(y_val)}")

# Calculate scale_pos_weight (handles class imbalance)
n_negative = (y_train == 0).sum()
n_positive = (y_train == 1).sum()
scale_pos_weight = n_negative / n_positive

print(f"\n2. Class Imbalance Handling:")
print(f"   Negative (normal): {n_negative}")
print(f"   Positive (failure): {n_positive}")
print(f"   Scale_pos_weight: {scale_pos_weight:.2f}")

# XGBoost hyperparameters
print(f"\n3. Training XGBoost with tuned hyperparameters...")
params = {
    'objective': 'binary:logistic',
    'eval_metric': 'aucpr',  # AUC-PR better for imbalanced
    'max_depth': 5,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'gamma': 0.1,
    'scale_pos_weight': scale_pos_weight,
    'seed': 42,
    'n_jobs': -1
}

print(f"   Hyperparameters:")
for k, v in params.items():
    print(f"      {k}: {v}")

# Train with early stopping
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)

evals = [(dtrain, 'train'), (dval, 'val')]
evals_result = {}

model = xgb.train(
    params,
    dtrain,
    num_boost_round=300,
    evals=evals,
    evals_result=evals_result,
    early_stopping_rounds=50,
    verbose_eval=50
)

print(f"\n   [OK] Training complete: {model.best_iteration + 1} boosting rounds")

# Evaluate
print(f"\n4. Model Evaluation:")

# Training set
y_train_pred = model.predict(dtrain)
train_auc = roc_auc_score(y_train, y_train_pred)
train_f1 = f1_score(y_train, (y_train_pred > 0.5).astype(int))
train_prec = precision_score(y_train, (y_train_pred > 0.5).astype(int))
train_rec = recall_score(y_train, (y_train_pred > 0.5).astype(int))

print(f"   Training Set:")
print(f"      AUC-ROC: {train_auc:.4f}")
print(f"      F1-Score: {train_f1:.4f}")
print(f"      Precision: {train_prec:.4f}")
print(f"      Recall: {train_rec:.4f}")

# Validation set
y_val_pred = model.predict(dval)
val_auc = roc_auc_score(y_val, y_val_pred)
val_f1 = f1_score(y_val, (y_val_pred > 0.5).astype(int))
val_prec = precision_score(y_val, (y_val_pred > 0.5).astype(int))
val_rec = recall_score(y_val, (y_val_pred > 0.5).astype(int))

print(f"   Validation Set:")
print(f"      AUC-ROC: {val_auc:.4f}")
print(f"      F1-Score: {val_f1:.4f}")
print(f"      Precision: {val_prec:.4f}")
print(f"      Recall: {val_rec:.4f}")

# Feature importance (SHAP)
print(f"\n5. Feature Importance (XGBoost native):")
importance = model.get_score(importance_type='weight')
top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
for feat, score in top_features:
    print(f"      {feat}: {score}")

# Save model
model_path = 'models/saved/failure_predictor_v1.pkl'
with open(model_path, 'wb') as f:
    pickle.dump({
        'model': model,
        'params': params,
        'train_auc': train_auc,
        'val_auc': val_auc,
        'n_features': X_train.shape[1],
        'version': '1.0'
    }, f)

print(f"\n[OK] Model saved: {model_path}")
print(f"   Size: {os.path.getsize(model_path) / (1024**2):.2f} MB")

print(f"\nMetrics Summary:")
print(f"   Algorithm: XGBoost")
print(f"   Training samples: {len(X_train)}")
print(f"   Features: {X_train.shape[1]}")
print(f"   Boosting rounds: {model.best_iteration + 1}")
print(f"   Validation AUC-ROC: {val_auc:.4f}")
print(f"   [OK] PASS: AUC > 0.75" if val_auc > 0.75 else "   [FAIL] FAIL: AUC <= 0.75")

print(f"\n[OK] Phase 2B.4 Complete!")
print(f"Next step: python models/train/03_train_rul.py")
