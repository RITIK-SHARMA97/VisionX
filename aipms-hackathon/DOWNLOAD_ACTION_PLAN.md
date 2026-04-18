# 📋 C-MAPSS Dataset Download - Complete Action Plan

**Status**: Ready for manual download  
**Date**: April 18, 2026  
**Project**: AIPMS Hackathon - Phase 2B

---

## 🎯 Your Mission (Choose ONE Path)

### 🟢 PATH 1: Fastest (Recommended - 5 minutes)

**Use the automated helper script** after downloading:

```powershell
# Step 1: Download from Kaggle (manually click Download button)
# https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
# File: nasa-cmaps.zip (~2 MB)

# Step 2: Run the setup helper (PowerShell)
cd c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon
.\setup_dataset.ps1 -ZipPath "C:\Users\sharm\Downloads\nasa-cmaps.zip"

# Step 3: Verify installation
python check_dataset.py

# Step 4: Start pipeline
python models/train/run_phase_2b.py
```

### 🟡 PATH 2: Manual (10 minutes)

**Classic copy-paste approach**:

1. Download: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
2. Extract ZIP file
3. Copy 6 `.txt` files to: `c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon\data\raw\`
4. Run: `python check_dataset.py`
5. Run: `python models/train/run_phase_2b.py`

### 🔵 PATH 3: Detailed Guide (Read First)

**If you want to understand everything**:

1. Read: [DOWNLOAD_CMAPSS_GUIDE.md](DOWNLOAD_CMAPSS_GUIDE.md)
2. Read: [QUICK_START_DOWNLOAD.md](QUICK_START_DOWNLOAD.md)
3. Follow the step-by-step instructions
4. Run verification and pipeline

---

## 📦 Files You Need to Copy

| File | Size | From Dataset |
|------|------|-------------|
| `train_FD001.txt` | 13.15 MB | Failure Condition 1 - Training data |
| `test_FD001.txt` | 5.30 MB | Failure Condition 1 - Test data |
| `RUL_FD001.txt` | 0.01 MB | Failure Condition 1 - Ground truth |
| `train_FD003.txt` | 13.71 MB | Failure Condition 3 - Training data |
| `test_FD003.txt` | 5.63 MB | Failure Condition 3 - Test data |
| `RUL_FD003.txt` | 0.01 MB | Failure Condition 3 - Ground truth |
| **TOTAL** | **~38 MB** | NASA C-MAPSS Dataset |

**Destination**: `c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon\data\raw\`

---

## 🛠️ Tools You Have

### 1. Verification Script
```powershell
python check_dataset.py
```
✅ Shows which files are present/missing  
✅ Validates file sizes  
✅ Estimates preprocessing time  

### 2. Setup Helper
```powershell
.\setup_dataset.ps1 -ZipPath "C:\path\to\nasa-cmaps.zip"
```
✅ Extracts ZIP automatically  
✅ Copies files to correct location  
✅ Shows progress  

### 3. Download Guide
📄 **DOWNLOAD_CMAPSS_GUIDE.md** - Comprehensive instructions  
📄 **QUICK_START_DOWNLOAD.md** - Quick reference card  

---

## ✅ Verification Checklist

After downloading and copying files, verify:

```powershell
# Check if files exist
ls C:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon\data\raw\*.txt

# Should show 6 files:
# train_FD001.txt
# test_FD001.txt
# RUL_FD001.txt
# train_FD003.txt
# test_FD003.txt
# RUL_FD003.txt

# Run verification script
python check_dataset.py
```

**Expected output:**
```
✓ VALID FILES FOUND:
  ✓ train_FD001.txt       13.15 MB
  ✓ test_FD001.txt         5.30 MB
  ✓ RUL_FD001.txt          0.01 MB
  ✓ train_FD003.txt       13.71 MB
  ✓ test_FD003.txt         5.63 MB
  ✓ RUL_FD003.txt          0.01 MB

✓ SUCCESS! All files ready
```

---

## 🚀 Next Steps After Verification

Once `check_dataset.py` shows "SUCCESS", run the ML pipeline:

```powershell
cd c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon
python models/train/run_phase_2b.py
```

### What It Does:
1. **Phase 2B.2**: Preprocess data (extract 56 features)
2. **Phase 2B.3**: Train anomaly detection model
3. **Phase 2B.4**: Train failure prediction model  
4. **Phase 2B.5**: Train RUL estimation model

### Expected Runtime:
- Preprocessing: ~10 minutes
- Anomaly Detection: ~5 minutes
- Failure Prediction: ~15 minutes
- RUL Estimation: ~20 minutes
- **Total**: ~50 minutes

### Output Files Created:
```
models/saved/
├── anomaly_model.pkl        ✓ Anomaly detector
├── failure_model.json       ✓ Failure predictor
└── rul_model.h5             ✓ RUL estimator

data/processed/
├── X_train.npy              ✓ Training features
├── y_train.npy              ✓ Training targets
└── ... (test data, scalers)
```

---

## 🔗 Download Links

| Resource | URL |
|----------|-----|
| **🎯 Kaggle Dataset** | https://www.kaggle.com/datasets/behrad3d/nasa-cmaps |
| **🏢 NASA Official** | https://data.nasa.gov/Aerospace/CMAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6 |
| **📖 Documentation** | See links below |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| [DOWNLOAD_CMAPSS_GUIDE.md](DOWNLOAD_CMAPSS_GUIDE.md) | **Comprehensive download & setup guide** |
| [QUICK_START_DOWNLOAD.md](QUICK_START_DOWNLOAD.md) | **Quick reference (3 steps)** |
| [PHASE_2B_COMPLETION.md](PHASE_2B_COMPLETION.md) | **Phase 2B implementation details** |
| [README_PHASE_2B.md](README_PHASE_2B.md) | **ML architecture & usage** |
| [check_dataset.py](check_dataset.py) | **Verification script** |
| [setup_dataset.ps1](setup_dataset.ps1) | **Automated setup helper** |

---

## ❓ Frequently Asked Questions

**Q: Can I download only FD001 (not FD003)?**  
A: Yes, but preprocessing will be incomplete. For the full pipeline, get both.

**Q: Where exactly do I put the files?**  
A: `c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon\data\raw\`

**Q: My ZIP extraction failed. What do I do?**  
A: Try: Right-click ZIP → Properties → Advanced → Uncheck "Read-only" → Extract

**Q: Do I need Kaggle account?**  
A: Yes, but it's free. You can also download from NASA official repository.

**Q: How much disk space do I need?**  
A: ~100 MB total (38 MB dataset + 50 MB processed data + 15 MB models)

**Q: Can I use the dataset from somewhere else?**  
A: Yes, as long as files have same names and format (space-separated values)

---

## 🎓 What Happens Next

### After Download ✓
- Preprocessing creates 56-dimensional feature vectors
- Data split into train/val/test sets
- Features normalized (0-1 range)

### After Training ✓
- **Anomaly Model**: Detects degradation
- **Failure Model**: Predicts failure probability
- **RUL Model**: Estimates remaining useful life

### After Phase 2B ✓
- Models saved and ready for Phase 3A (API)
- Dashboard can consume APIs in Phase 3B
- Complete ML pipeline operational

---

## 🔴 Troubleshooting

| Error | Solution |
|-------|----------|
| `✗ MISSING FILES` | Download dataset to `data/raw/` |
| `Permission denied` | Right-click ZIP → Properties → Uncheck "Read-only" |
| `Path not found` | Verify directory path is correct |
| `No module named 'pandas'` | Packages already installed, just needs dataset |
| `LSTM training too slow` | Normal - RUL LSTM takes ~20 min, can run on GPU if available |

---

## ✨ Quick Commands Reference

```powershell
# Navigate to project
cd c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon

# Check current files
ls data\raw\

# Run helper script
.\setup_dataset.ps1 -Help

# Verify dataset ready
python check_dataset.py

# Start training pipeline
python models\train\run_phase_2b.py

# Check progress manually
ls -lah models\saved\      # Look for generated models
ls -lah data\processed\    # Look for processed data
```

---

## 🎯 Success Criteria

✅ All 6 files present in `data/raw/`  
✅ `check_dataset.py` shows "SUCCESS"  
✅ `run_phase_2b.py` executes without errors  
✅ Models saved to `models/saved/`  
✅ Data processed to `data/processed/`  

---

**Ready to download? Start with [QUICK_START_DOWNLOAD.md](QUICK_START_DOWNLOAD.md)!** 🚀

---

*Generated: 2026-04-18 | Phase 2B ML Data Preparation | AIPMS Hackathon*
