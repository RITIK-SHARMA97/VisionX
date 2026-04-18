# C-MAPSS Dataset Manual Download Guide

## Overview
The C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) dataset contains simulated data for turbofan engine degradation and remaining useful life (RUL) prediction.

**Dataset Location**: [Kaggle C-MAPSS Dataset](https://www.kaggle.com/datasets/behrad3d/nasa-cmaps)  
**Alternative**: [NASA Official Repository](https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6)

---

## Step 1: Download from Kaggle

### Method A: Kaggle.com Website (Easiest)

1. Go to: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
2. Click the **Download** button (upper right)
3. This will download `nasa-cmaps.zip` (~2 MB)
4. Extract the ZIP file

### Method B: Kaggle API (if you have credentials)

```powershell
# After configuring credentials:
kaggle datasets download -d behrad3d/nasa-cmaps --unzip --path data/raw
```

**To set up Kaggle API:**
1. Go to: https://www.kaggle.com/settings/account
2. Click "Create New API Token" (downloads `kaggle.json`)
3. Place `kaggle.json` in: `C:\Users\<YourUsername>\.kaggle\`
4. Make sure file permissions allow read access

---

## Step 2: Verify Downloaded Files

The ZIP should contain these 6 files:

```
train_FD001.txt       (13.1 MB) - Training data for failure condition 1
test_FD001.txt        (5.3 MB)  - Test data for failure condition 1
RUL_FD001.txt         (5 KB)    - Remaining useful life ground truth

train_FD003.txt       (13.7 MB) - Training data for failure condition 3
test_FD003.txt        (5.6 MB)  - Test data for failure condition 3
RUL_FD003.txt         (5 KB)    - Remaining useful life ground truth
```

---

## Step 3: Extract to Project Directory

1. Extract the downloaded ZIP file
2. Copy all 6 `.txt` files to:
   ```
   aipms-hackathon/data/raw/
   ```

**Your directory structure should look like:**
```
aipms-hackathon/
├── data/
│   ├── raw/
│   │   ├── train_FD001.txt       ✓ Place files here
│   │   ├── test_FD001.txt
│   │   ├── RUL_FD001.txt
│   │   ├── train_FD003.txt
│   │   ├── test_FD003.txt
│   │   └── RUL_FD003.txt
│   ├── processed/                ✓ (auto-created)
│   └── scalers/                  ✓ (auto-created)
├── models/
│   └── train/
│       ├── 00_download.py
│       ├── 01_preprocess.py
│       ├── 02_train_anomaly.py
│       ├── 02_train_failure.py
│       ├── 03_train_rul.py
│       └── run_phase_2b.py
```

---

## Step 4: Verify Installation

Run the verification script:
```powershell
cd c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon
python models/train/00_download.py
```

**Expected output:**
```
================================================================================
VERIFICATION
================================================================================

✓ Found files:
  ✓ train_FD001.txt (13.15 MB)
  ✓ test_FD001.txt (5.30 MB)
  ✓ RUL_FD001.txt (0.01 MB)
  ✓ train_FD003.txt (13.71 MB)
  ✓ test_FD003.txt (5.63 MB)
  ✓ RUL_FD003.txt (0.01 MB)

✓ All required files present!

Next step: python models/train/01_preprocess.py
```

---

## Step 5: Run the ML Pipeline

Once files are verified, execute the complete training pipeline:

```powershell
# Run all phases at once:
python models/train/run_phase_2b.py

# OR run individual phases:
python models/train/01_preprocess.py      # ~10 min - Feature engineering
python models/train/02_train_anomaly.py   # ~5 min  - Anomaly detection
python models/train/02_train_failure.py   # ~15 min - Failure prediction
python models/train/03_train_rul.py       # ~20 min - RUL estimation
```

---

## File Formats

Each dataset file contains space-separated values:

### train_FD001.txt format:
```
engine_id cycle op_setting_1 op_setting_2 op_setting_3 sensor_1 sensor_2 ... sensor_21
1         1     -0.0007       -0.0004       100         518.67   644.12  ...  8.4195
1         2     0.0019        -0.0003       100         518.67   642.15  ...  8.4318
...
```

### RUL_FD001.txt format:
```
130.0   (RUL in cycles for first engine)
133.0   (RUL in cycles for second engine)
...
```

---

## Troubleshooting

### Problem: "Permission denied" when extracting
**Solution**: Right-click ZIP → Properties → Advanced → Uncheck "Read-only" → Extract

### Problem: Files extracted to wrong location
**Solution**: Manually move all `.txt` files to `data/raw/` directory

### Problem: Missing some files after extraction
**Solution**: Verify all 6 files are in the ZIP:
- 2 for FD001: train, test, RUL
- 2 for FD003: train, test, RUL

### Problem: Download stuck or interrupted
**Solution**: Re-download from Kaggle and try again

---

## Alternative: NASA Official Source

If Kaggle download doesn't work, download from NASA:
1. Go to: https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6
2. Download dataset in CSV or text format
3. Place files in `data/raw/` with the same names

---

## Quick Links

| Resource | URL |
|----------|-----|
| Kaggle Dataset | https://www.kaggle.com/datasets/behrad3d/nasa-cmaps |
| NASA Repository | https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6 |
| Kaggle API Setup | https://www.kaggle.com/settings/account |
| Python Kaggle Docs | https://github.com/Kaggle/kaggle-api |

---

## Expected Total Size
- **Compressed (ZIP)**: ~2 MB
- **Extracted**: ~38 MB
- **Total with processed data**: ~100+ MB after preprocessing

---

**Next Steps**: After placing files in `data/raw/`, run:
```powershell
python models/train/run_phase_2b.py
```
