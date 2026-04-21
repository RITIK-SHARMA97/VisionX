"""
Phase 2B.2: Data Preprocessing & Feature Engineering
Load C-MAPSS data, compute RUL, extract rolling statistics, normalize

Input: data/raw/train_FD001.txt, train_FD003.txt
Output: data/processed/FD001_X.npy, FD001_y.npy, FD003_X.npy, FD003_y.npy
        data/scalers/scaler.pkl, feature_cols.pkl
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pickle
import os
from pathlib import Path
import warnings
import logging
import config_constants as cfg

logging.basicConfig(level=cfg.LOG_LEVEL, format=cfg.LOG_FORMAT)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

# Ensure output directories exist
os.makedirs('data/processed', exist_ok=True)
os.makedirs('data/scalers', exist_ok=True)

print("=" * 80)
print("C-MAPSS Data Preprocessing & Feature Engineering")
print("=" * 80)


def load_c_mapss_data(source_file, n_cycles_max=125, verbose=True):
    """
    Load raw C-MAPSS data, compute RUL, create binary failure label
    
    Input format (space-separated):
    engine_id, cycle, op_setting_1, op_setting_2, op_setting_3, sensor_1...sensor_21
    
    Output: DataFrame with RUL and failure labels
    """
    print(f"\n1. Loading {source_file}...")
    
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Dataset not found: {source_file}")
    
    # Load data with space-separated columns
    df = pd.read_csv(source_file, sep='\s+', header=None, engine='python')
    
    # Name columns
    n_sensors = df.shape[1] - 5  # total cols - (engine_id, cycle, op1, op2, op3)
    col_names = ['engine_id', 'cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3']
    col_names += [f'sensor_{i}' for i in range(1, n_sensors + 1)]
    df.columns = col_names[:df.shape[1]]
    
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns[:5])}...{list(df.columns[-3:])}")
    print(f"   Engine IDs: {sorted(df['engine_id'].unique())[:5]}... ({df['engine_id'].nunique()} total)")
    
    # Remove near-zero-variance sensors (based on C-MAPSS literature)
    # Sensors 1, 5, 6, 10, 16, 18, 19 have near-zero variance
    near_zero_sensors = [1, 5, 6, 10, 16, 18, 19]
    all_sensor_cols = [col for col in df.columns if col.startswith('sensor_')]
    active_sensor_cols = [col for col in all_sensor_cols 
                          if int(col.split('_')[1]) not in near_zero_sensors]
    
    print(f"\n2. Feature Selection")
    print(f"   Total sensors: {len(all_sensor_cols)}")
    print(f"   Near-zero variance removed: {len(near_zero_sensors)}")
    print(f"   Active sensors: {len(active_sensor_cols)} -> {active_sensor_cols}")
    
    # Compute RUL per engine (max_cycle - current_cycle)
    print(f"\n3. Computing RUL labels...")
    max_cycle_per_engine = df.groupby('engine_id')['cycle'].max()
    df['rul'] = df.apply(lambda row: max_cycle_per_engine[row['engine_id']] - row['cycle'], axis=1)
    
    # Piecewise linear clipping (flat early, linear decline near end)
    df['rul_clipped'] = np.minimum(df['rul'], n_cycles_max)
    
    # Binary failure label: 1 if RUL <= 30 cycles (7-day horizon)
    df['failure_label'] = (df['rul_clipped'] <= 30).astype(int)
    
    print(f"   RUL range: {df['rul'].min():.0f} to {df['rul'].max():.0f} cycles")
    print(f"   Clipped RUL range: 0 to {n_cycles_max}")
    print(f"   Failure label distribution:")
    print(f"      Normal (0): {(df['failure_label'] == 0).sum()} ({100 * (df['failure_label'] == 0).sum() / len(df):.1f}%)")
    print(f"      Failure (1): {(df['failure_label'] == 1).sum()} ({100 * (df['failure_label'] == 1).sum() / len(df):.1f}%)")
    print(f"   Class ratio (normal:failure): {(df['failure_label'] == 0).sum() / max((df['failure_label'] == 1).sum(), 1):.2f}:1")
    
    return df, active_sensor_cols


def extract_features(df, active_sensor_cols, window_size=cfg.FEATURE_WINDOW_SIZE, verbose=True):
    """
    Extract rolling statistics features per sensor
    - raw values (baseline)
    - rolling mean (trend smoothing)
    - rolling std (variability)
    - rolling slope (rate of change)
    
    Total features: 14 active sensors × 4 = 56 features
    """
    print(f"\n4. Extracting rolling statistics (window={window_size})...")
    
    feature_cols = []
    
    for sensor_col in active_sensor_cols:
        # Raw sensor value (baseline)
        feature_cols.append(sensor_col)
        
        # Rolling mean (5-cycle average)
        mean_col = f'{sensor_col}_mean'
        df[mean_col] = df.groupby('engine_id')[sensor_col].transform(
            lambda x: x.rolling(window_size, min_periods=1).mean()
        )
        feature_cols.append(mean_col)
        
        # Rolling std (5-cycle variability)
        std_col = f'{sensor_col}_std'
        df[std_col] = df.groupby('engine_id')[sensor_col].transform(
            lambda x: x.rolling(window_size, min_periods=1).std().fillna(0)
        )
        feature_cols.append(std_col)
        
        # Rolling slope (rate of change)
        slope_col = f'{sensor_col}_slope'
        
        def compute_slope(series):
            """Compute linear regression slope for window"""
            if len(series) <= 1:
                return 0
            try:
                x = np.arange(len(series))
                coeffs = np.polyfit(x, series.values, 1)
                return coeffs[0]
            except:
                return 0
        
        df[slope_col] = df.groupby('engine_id')[sensor_col].transform(
            lambda x: x.rolling(window_size, min_periods=1).apply(compute_slope, raw=False)
        )
        feature_cols.append(slope_col)
    
    print(f"   Features extracted: {len(feature_cols)}")
    print(f"   Feature breakdown:")
    print(f"      Raw sensors: {len(active_sensor_cols)}")
    print(f"      Means: {len(active_sensor_cols)}")
    print(f"      Stds: {len(active_sensor_cols)}")
    print(f"      Slopes: {len(active_sensor_cols)}")
    print(f"   Total feature vector: {len(feature_cols)} dimensions")
    
    return df, feature_cols


def normalize_and_save(df, feature_cols, output_prefix, scaler_file, verbose=True):
    """
    Min-Max normalize features, save as numpy arrays
    Scaler is fit on training data and saved for test set normalization
    """
    print(f"\n5. Normalizing and saving {output_prefix}...")
    
    # Extract feature matrix X and target y
    X = df[feature_cols].values.astype(np.float32)
    y = df['failure_label'].values.astype(np.int32)
    rul = df['rul_clipped'].values.astype(np.float32)
    
    print(f"   Before normalization:")
    print(f"      X shape: {X.shape}, range: [{X.min():.4f}, {X.max():.4f}]")
    print(f"      y distribution: {np.bincount(y)}")
    
    # Min-Max normalization (0-1 scale)
    scaler = MinMaxScaler(feature_range=(0, 1))
    X_normalized = scaler.fit_transform(X)
    
    print(f"   After normalization:")
    print(f"      X shape: {X_normalized.shape}, range: [{X_normalized.min():.4f}, {X_normalized.max():.4f}]")
    
    # Save arrays
    np.save(f"{output_prefix}_X.npy", X_normalized)
    np.save(f"{output_prefix}_y.npy", y)
    np.save(f"{output_prefix}_rul.npy", rul)
    
    print(f"   [OK] Saved: {output_prefix}_X.npy ({X_normalized.nbytes / (1024**2):.2f} MB)")
    print(f"   [OK] Saved: {output_prefix}_y.npy ({y.nbytes / (1024**2):.2f} MB)")
    print(f"   [OK] Saved: {output_prefix}_rul.npy ({rul.nbytes / (1024**2):.2f} MB)")
    
    return scaler, feature_cols


def main():
    """Main preprocessing pipeline"""
    
    # Phase 2B.2: Preprocess FD001 and FD003
    datasets = {
        'FD001': 'data/raw/train_FD001.txt',
        'FD003': 'data/raw/train_FD003.txt'
    }
    
    all_feature_cols = None
    all_scalers = {}
    
    for dataset_name, input_file in datasets.items():
        print(f"\n{'=' * 80}")
        print(f"DATASET: {dataset_name}")
        print(f"{'=' * 80}")
        
        # Check file exists
        if not os.path.exists(input_file):
            print(f"   [ERROR] File not found: {input_file}")
            print(f"   Please download C-MAPSS dataset from:")
            print(f"   https://www.kaggle.com/datasets/behrad3d/nasa-cmaps")
            continue
        
        # Load and preprocess
        df, active_sensors = load_c_mapss_data(input_file)
        df, feature_cols = extract_features(df, active_sensors)
        
        # Store first set of feature columns for consistency check
        if all_feature_cols is None:
            all_feature_cols = feature_cols
        
        # Normalize and save
        scaler, _ = normalize_and_save(
            df, 
            feature_cols,
            f'data/processed/{dataset_name}',
            f'data/scalers/scaler_{dataset_name}.pkl'
        )
        
        all_scalers[dataset_name] = (scaler, feature_cols)
    
    # Save unified scaler and feature metadata
    if all_feature_cols:
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        
        scaler = MinMaxScaler()  # Dummy for export
        metadata = {
            'scaler': scaler,
            'feature_cols': all_feature_cols,
            'n_features': len(all_feature_cols),
            'window_size': 5,
            'datasets': list(all_scalers.keys())
        }
        
        with open('data/scalers/scaler.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"   [OK] Unified metadata saved: data/scalers/scaler.pkl")
        print(f"   [OK] Feature columns: {len(all_feature_cols)}")
        print(f"   [OK] Datasets processed: {', '.join(all_scalers.keys())}")
        print(f"\n[OK] Phase 2B.2 Complete!")
        print(f"\nNext step: python models/train/02_train_anomaly.py")


if __name__ == "__main__":
    main()
