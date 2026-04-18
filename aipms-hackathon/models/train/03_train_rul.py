"""
Phase 2B.5: Train RUL Estimation Model (LSTM)
Estimates Remaining Useful Life using recurrent neural networks

Model: PyTorch LSTM regression
Input: data/processed/FD001_X.npy, FD001_rul.npy
Output: models/saved/rul_estimator_v1.pt

Algorithm: LSTM (Long Short-Term Memory) learns temporal degradation patterns
over 50-timestep sequences. Asymmetric loss penalizes late predictions 1.5×
to encourage conservative estimates.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pickle
import os

os.makedirs('models/saved', exist_ok=True)

print("=" * 80)
print("Phase 2B.5: Training RUL Estimation Model (LSTM)")
print("=" * 80)

# Check GPU availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n1. Device: {device}")

# Load data
print(f"\n2. Loading training data...")
try:
    X_train_all = np.load('data/processed/FD001_X.npy').astype(np.float32)
    rul_train_all = np.load('data/processed/FD001_rul.npy').astype(np.float32)
    print(f"   [OK] Loaded: X={X_train_all.shape}, RUL={rul_train_all.shape}")
except FileNotFoundError as e:
    print(f"   [ERROR] Missing data: {e}")
    exit(1)

# Create LSTM sequences
print(f"\n3. Creating LSTM sequences...")
seq_length = 50
sequences_X = []
sequences_y = []

for i in range(len(X_train_all) - seq_length):
    seq = X_train_all[i:i + seq_length]
    target = rul_train_all[i + seq_length]
    sequences_X.append(seq)
    sequences_y.append(target)

X_lstm = np.array(sequences_X)
y_lstm = np.array(sequences_y)

print(f"   [OK] Sequences created: X={X_lstm.shape}, y={y_lstm.shape}")
print(f"   Sequence length: {seq_length} timesteps")
print(f"   Features per timestep: {X_lstm.shape[2]}")

# Train-validation split
train_size = int(0.8 * len(X_lstm))
X_train = torch.from_numpy(X_lstm[:train_size]).to(device)
y_train = torch.from_numpy(y_lstm[:train_size]).unsqueeze(1).to(device)
X_val = torch.from_numpy(X_lstm[train_size:]).to(device)
y_val = torch.from_numpy(y_lstm[train_size:]).unsqueeze(1).to(device)

print(f"   Train: X={X_train.shape}, y={y_train.shape}")
print(f"   Val: X={X_val.shape}, y={y_val.shape}")

# LSTM Model Definition
class RULEstimator(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super(RULEstimator, self).__init__()
        self.batch_norm = nn.BatchNorm1d(input_size)
        self.lstm1 = nn.LSTM(input_size, hidden_size, batch_first=True, dropout=0.2)
        self.lstm2 = nn.LSTM(hidden_size, hidden_size // 2, batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size // 2, 16)
        self.fc2 = nn.Linear(16, 1)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        # Apply batch norm per sample
        batch_size, seq_len, n_features = x.shape
        x_bn = self.batch_norm(x.view(-1, n_features)).view(batch_size, seq_len, n_features)
        
        # LSTM layers
        lstm1_out, _ = self.lstm1(x_bn)
        lstm2_out, (h, c) = self.lstm2(lstm1_out)
        
        # Use final hidden state
        final_hidden = h[-1]  # (batch_size, hidden_size // 2)
        
        # Dense layers
        fc1_out = self.relu(self.fc1(final_hidden))
        rul_pred = self.relu(self.fc2(fc1_out))  # RUL >= 0
        
        return rul_pred

print(f"\n4. Model Architecture:")
model = RULEstimator(input_size=X_train.shape[2])
model = model.to(device)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"   LSTM-based RUL Estimator")
print(f"   Hidden layers: [64, 32]")
print(f"   Total parameters: {total_params:,}")
print(f"   Trainable parameters: {trainable_params:,}")

# Asymmetric loss function
class AsymmetricRULLoss(nn.Module):
    def __init__(self, alpha=1.5):
        super().__init__()
        self.alpha = alpha  # Penalty multiplier for overestimation
    
    def forward(self, y_pred, y_true):
        """
        Asymmetric MSE: penalize late predictions (overestimates) more
        w = 1.5 if pred > true (dangerous - late warning)
        w = 1.0 if pred <= true (safe - early warning)
        """
        error = y_pred - y_true
        weights = torch.where(error > 0, self.alpha * torch.ones_like(error), torch.ones_like(error))
        loss = torch.mean(weights * (error ** 2))
        return loss

criterion = AsymmetricRULLoss(alpha=1.5)
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10, verbose=False)

print(f"\n5. Training Configuration:")
print(f"   Loss: AsymmetricRULLoss (alpha=1.5)")
print(f"   Optimizer: Adam (lr=0.001)")
print(f"   Scheduler: ReduceLROnPlateau (patience=10)")
print(f"   Early stopping: patience=15")

# Training loop
print(f"\n6. Training LSTM RUL Estimator...")
epochs = 100
batch_size = 256
best_val_rmse = float('inf')
patience = 15
patience_counter = 0

train_loader = DataLoader(
    list(zip(X_train, y_train)),
    batch_size=batch_size,
    shuffle=True
)

val_loader = DataLoader(
    list(zip(X_val, y_val)),
    batch_size=batch_size
)

for epoch in range(epochs):
    # Training
    model.train()
    train_loss = 0
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    train_loss /= len(train_loader)
    
    # Validation
    model.eval()
    val_loss = 0
    val_preds = []
    val_trues = []
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch)
            val_loss += loss.item()
            val_preds.append(y_pred.cpu().numpy())
            val_trues.append(y_batch.cpu().numpy())
    
    val_loss /= len(val_loader)
    val_preds = np.concatenate(val_preds)
    val_trues = np.concatenate(val_trues)
    
    val_rmse = np.sqrt(np.mean((val_preds - val_trues) ** 2))
    val_mae = np.mean(np.abs(val_preds - val_trues))
    
    # Update learning rate
    scheduler.step(val_loss)
    
    # Early stopping
    if val_rmse < best_val_rmse:
        best_val_rmse = val_rmse
        patience_counter = 0
        best_epoch = epoch
    else:
        patience_counter += 1
    
    if (epoch + 1) % 20 == 0:
        print(f"   Epoch {epoch + 1:3d}: train_loss={train_loss:.4f}, "
              f"val_loss={val_loss:.4f}, val_rmse={val_rmse:.2f}, val_mae={val_mae:.2f}")
    
    if patience_counter >= patience:
        print(f"   [OK] Early stopping at epoch {epoch + 1}")
        break

print(f"\n7. Final Validation Metrics:")
print(f"   Best epoch: {best_epoch + 1}")
print(f"   RMSE: {best_val_rmse:.2f} cycles")
print(f"   MAE: {val_mae:.2f} cycles")
print(f"   [OK] PASS: RMSE < 30 cycles" if best_val_rmse < 30 else f"   [FAIL] FAIL: RMSE >= 30")

# Save model
model_path = 'models/saved/rul_estimator_v1.pt'
torch.save({
    'model_state': model.state_dict(),
    'model_arch': {
        'input_size': X_train.shape[2],
        'hidden_size': 64
    },
    'metrics': {
        'val_rmse': float(best_val_rmse),
        'val_mae': float(val_mae),
        'best_epoch': int(best_epoch)
    },
    'version': '1.0'
}, model_path)

print(f"\n[OK] Model saved: {model_path}")
print(f"   Size: {os.path.getsize(model_path) / (1024**2):.2f} MB")

print(f"\nMetrics Summary:")
print(f"   Algorithm: LSTM (PyTorch)")
print(f"   Sequence length: {seq_length}")
print(f"   Training samples: {len(X_train)}")
print(f"   Validation samples: {len(X_val)}")
print(f"   RMSE: {best_val_rmse:.2f} cycles")

print(f"\n[OK] Phase 2B.5 Complete!")
print(f"\nAll models trained successfully!")
