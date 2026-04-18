# ⚡ QUICK START: Download C-MAPSS Dataset

## 🎯 What You Need to Do (3 Steps)

### Step 1: Download the Dataset
**Go to**: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps

Click the **"Download"** button (blue button, upper right corner)
- File size: ~2 MB
- Downloads as: `nasa-cmaps.zip`

### Step 2: Extract the ZIP File
- Right-click `nasa-cmaps.zip`
- Select "Extract All"
- Extract to any temporary folder

### Step 3: Copy 6 Files to Project
Copy these 6 files from the extracted folder:
```
train_FD001.txt
test_FD001.txt
RUL_FD001.txt
train_FD003.txt
test_FD003.txt
RUL_FD003.txt
```

**Paste them into**:
```
C:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon\data\raw\
```

---

## ✅ Verify Installation

After copying files, open PowerShell and run:

```powershell
cd c:\Users\sharm\Downloads\BIT-SINDRI\aipms-hackathon
python check_dataset.py
```

**Expected output**:
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

## 🚀 Run ML Pipeline

Once verification passes, execute:

```powershell
python models/train/run_phase_2b.py
```

**This will**:
1. Preprocess data (10 min)
2. Train anomaly detection (5 min)
3. Train failure prediction (15 min)
4. Train RUL estimation (20 min)
5. Save all 3 models to `models/saved/`

**Total runtime**: ~50 minutes

---

## 📊 Expected Output Files

After pipeline completes:

```
models/saved/
├── anomaly_model.pkl         (8 MB)   - Isolation Forest
├── failure_model.json        (2 MB)   - XGBoost
├── rul_model.h5              (15 MB)  - LSTM
└── metadata.json             (50 KB)  - Training info

data/processed/
├── X_train.npy              (100 MB)  - Features
├── y_train.npy              (10 MB)   - Targets
├── X_test.npy               (45 MB)   - Test features
└── y_test.npy               (5 MB)    - Test targets

data/scalers/
└── scaler.pkl               (2 MB)    - Min-Max Normalizer
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't find Download button on Kaggle | Try logging out and back in to Kaggle |
| ZIP file won't extract | Right-click → Properties → Advanced → Uncheck "Read-only" |
| Files extracted to wrong location | Manually cut/paste to `data/raw/` |
| `check_dataset.py` still shows missing files | Double-check all 6 files are copied |
| Python script not found | Verify you're in the correct directory |

---

## 📚 Additional Resources

- **Full Download Guide**: [DOWNLOAD_CMAPSS_GUIDE.md](DOWNLOAD_CMAPSS_GUIDE.md)
- **Phase 2B Details**: [PHASE_2B_COMPLETION.md](PHASE_2B_COMPLETION.md)
- **Quick Start**: [README_PHASE_2B.md](README_PHASE_2B.md)

---

## 💡 Pro Tips

✅ **Create a dedicated folder** for the ZIP while extracting (keeps things organized)
✅ **Copy ALL 6 files** - pipeline needs both FD001 and FD003
✅ **Verify after copying** - run `check_dataset.py` before starting pipeline
✅ **Keep original ZIP** - good for re-downloading if needed

---

## 🔄 Resume from Last Known Point

If anything goes wrong, you can always:
1. Delete files from `data/raw/` 
2. Re-download and extract
3. Run `check_dataset.py` again
4. Start the pipeline fresh

All preprocessing is reproducible with seed=42!

---

**Next**: Download the dataset → Run verification → Start pipeline! 🚀
