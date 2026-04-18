"""
Phase 2B.3: Train Anomaly Detection Model (Isolation Forest)
Detects equipment anomalies using unsupervised learning

Model: scikit-learn IsolationForest
Input: data/processed/FD001_X.npy
Output: models/saved/anomaly_detector_v1.pkl

Algorithm: Isolation Forest builds random trees - anomalies have shorter average
path length and are isolated quickly. No labeled data needed.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
from pathlib import Path

os.makedirs('models/saved', exist_ok=True)

print("=" * 80)
print("Phase 2B.3: Training Anomaly Detection Model (Isolation Forest)")
print("=" * 80)

# Load preprocessed data
print("\n1. Loading training data...")
try:
    X_train = np.load('data/processed/FD001_X.npy')
    print(f"   [OK] Loaded X_train: shape={X_train.shape}, dtype={X_train.dtype}")
except FileNotFoundError:
    print("   [ERROR] Missing data/processed/FD001_X.npy")
    print("   Run: python models/train/01_preprocess.py")
    exit(1)

print(f"\n2. Training Isolation Forest...")
print(f"   Parameters:")
print(f"      n_estimators: 200 (trees)")
print(f"      max_samples: 256")
print(f"      contamination: 0.05 (expected anomaly rate)")
print(f"      max_features: 1.0 (all)")
print(f"      random_state: 42 (reproducibility)")

# Train Isolation Forest
model = IsolationForest(
    n_estimators=200,
    max_samples=256,
    contamination=0.05,
    max_features=1.0,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

model.fit(X_train)

print(f"\n3. Model Statistics:")
print(f"   Offset: {model.offset_:.4f}")
print(f"   Decision boundary: {model.offset_:.4f}")
print(f"   n_features: {model.n_features_in_}")

# Compute anomaly scores (negative scores → anomaly)
# sklearn's IsolationForest returns -1 for anomalies, +1 for normal
scores = model.decision_function(X_train)
anomalies = model.predict(X_train)

print(f"\n4. Evaluation on Training Data:")
print(f"   Decision function range: [{scores.min():.4f}, {scores.max():.4f}]")
print(f"   Normal samples: {(anomalies == 1).sum()} ({100 * (anomalies == 1).sum() / len(anomalies):.1f}%)")
print(f"   Anomalies: {(anomalies == -1).sum()} ({100 * (anomalies == -1).sum() / len(anomalies):.1f}%)")

# Anomaly score mapping (convert to 0-1 scale for thresholding)
# Lower decision function → higher anomaly score
anomaly_scores = 1.0 / (1.0 + np.exp(scores))  # Sigmoid transformation
print(f"\n5. Anomaly Score Calibration (sigmoid-transformed):")
print(f"   Score range: [{anomaly_scores.min():.4f}, {anomaly_scores.max():.4f}]")
print(f"   Mean score (normal): {anomaly_scores[anomalies == 1].mean():.4f}")
print(f"   Mean score (anomaly): {anomaly_scores[anomalies == -1].mean():.4f}")

# Thresholds for alert levels
threshold_warning = 0.40
threshold_critical = 0.70

n_warning = (anomaly_scores >= threshold_warning).sum()
n_critical = (anomaly_scores >= threshold_critical).sum()

print(f"\n6. Alert Threshold Distribution:")
print(f"   Warning (0.40-0.70): {n_warning - n_critical} samples")
print(f"   Critical (>=0.70): {n_critical} samples")

# Save model
model_path = 'models/saved/anomaly_detector_v1.pkl'
with open(model_path, 'wb') as f:
    pickle.dump({
        'model': model,
        'thresholds': {
            'warning': threshold_warning,
            'critical': threshold_critical
        },
        'n_features': model.n_features_in_,
        'version': '1.0'
    }, f)

print(f"\n[OK] Model saved: {model_path}")
print(f"   Size: {os.path.getsize(model_path) / 1024:.2f} KB")

print(f"\nMetrics Summary:")
print(f"   Algorithm: IsolationForest")
print(f"   Training samples: {len(X_train)}")
print(f"   Features: {model.n_features_in_}")
print(f"   Trees: 200")
print(f"   Expected anomaly rate: 5%")

print(f"\n[OK] Phase 2B.3 Complete!")
print(f"Next step: python models/train/02_train_failure.py")
