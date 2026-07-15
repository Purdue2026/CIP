import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

DATA_PATH = 'data/processed/dataset_stage2.csv'
RESULT_PATH = 'ML/results/multistep_comparison_results.txt'
OUT_DIR = 'ML/plots'

FEATURE_COLS = ['비플럭스', '운영차압', '원수 수온', '원수 탁도', '원수 TDS', '원수 pH', '유입압력', '생산량', 'rain', 'temp']
TARGET_COL = '비플럭스'
TRAINVAL_CYCLES = [1, 2, 3, 4, 5, 6, 7, 8]
TEST_CYCLES = [9, 10]

INPUT_WINDOW = 168     # 과거 168시간 (7일)
FORECAST_HORIZON = 24  # 이후 24시간을 한 번에 예측

# 모델 파라미터
RIDGE_ALPHA = 10
LSTM_HIDDEN = 32
LSTM_LAYERS = 2
LSTM_LR = 1e-3
LSTM_EPOCHS = 150
LSTM_SEEDS = [0, 1, 2, 3, 7, 42, 100, 123, 777, 999]

lines = []


def log(msg=''):
    print(msg)
    lines.append(str(msg))


def make_multistep_sequences(df, feature_cols, target_col, input_window, horizon):
    X, Y, dates = [], [], []

    for cid, g in df.groupby('cycle_id'):
        feats = g[feature_cols].to_numpy()
        target = g[target_col].to_numpy()
        date_arr = g['Date'].to_numpy()
        n = len(g)
        for i in range(n - input_window - horizon + 1):
            X.append(feats[i:i + input_window])
            Y.append(target[i + input_window: i + input_window + horizon])
            dates.append(date_arr[i + input_window])  # 예측 구간의 시작 시각
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32), np.array(dates)


class SeqDataset(Dataset):
    def __init__(self, X, Y):
        self.X = torch.from_numpy(X)
        self.Y = torch.from_numpy(Y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]


class LSTMMultiStep(nn.Module):
    def __init__(self, n_features, hidden_size, num_layers, horizon):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden_size, num_layers=num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def train_lstm(X, Y, n_features, horizon, seed):
    torch.manual_seed(seed)
    loader = DataLoader(SeqDataset(X, Y), batch_size=64, shuffle=True)

    model = LSTMMultiStep(n_features, LSTM_HIDDEN, LSTM_LAYERS, horizon)
    optimizer = torch.optim.Adam(model.parameters(), lr=LSTM_LR)
    loss_fn = nn.MSELoss()
    for _ in range(LSTM_EPOCHS):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()

    return model


def predict_lstm(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(X)).numpy()


def evaluate_multistep(name, Y_true, Y_pred, results):
    rmse = mean_squared_error(Y_true.flatten(), Y_pred.flatten()) ** 0.5
    mae = mean_absolute_error(Y_true.flatten(), Y_pred.flatten())
    r2 = r2_score(Y_true.flatten(), Y_pred.flatten())

    results[name] = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
    log(f'[{name}] 전체(1~24시간 후 통합) RMSE={rmse:.4f}  MAE={mae:.4f}  R2={r2:.4f}')

    horizon_rmse, horizon_r2 = [], []
    for h in range(Y_true.shape[1]):
        horizon_rmse.append(mean_squared_error(Y_true[:, h], Y_pred[:, h]) ** 0.5)
        horizon_r2.append(r2_score(Y_true[:, h], Y_pred[:, h]))
    return horizon_rmse, horizon_r2


log('=' * 70)
log(f'비플럭스 다중 시점 예측 — Ridge vs LSTM (입력 {INPUT_WINDOW}시간 -> 출력 {FORECAST_HORIZON}시간, 1시간씩 슬라이딩)')
log('=' * 70)

# ------------------------------------------------------------
# 1) 데이터 로드, 시퀀스 생성
# ------------------------------------------------------------
df = pd.read_csv(DATA_PATH, parse_dates=['Date'])
df = df[df['is_operating']].reset_index(drop=True)

trainval_df = df[df['cycle_id'].isin(TRAINVAL_CYCLES)].reset_index(drop=True)
test_df = df[df['cycle_id'].isin(TEST_CYCLES)].reset_index(drop=True)

scaler = StandardScaler().fit(trainval_df[FEATURE_COLS])
trainval_scaled = trainval_df.copy()
trainval_scaled[FEATURE_COLS] = scaler.transform(trainval_df[FEATURE_COLS])
test_scaled = test_df.copy()
test_scaled[FEATURE_COLS] = scaler.transform(test_df[FEATURE_COLS])

trainval_scaled['target_orig'] = trainval_df[TARGET_COL].to_numpy()
test_scaled['target_orig'] = test_df[TARGET_COL].to_numpy()

X_train, Y_train, _ = make_multistep_sequences(trainval_scaled, FEATURE_COLS, 'target_orig', INPUT_WINDOW, FORECAST_HORIZON)
X_test, Y_test, test_dates = make_multistep_sequences(test_scaled, FEATURE_COLS, 'target_orig', INPUT_WINDOW, FORECAST_HORIZON)
log(f'train+val 샘플: {X_train.shape}  (사이클 {TRAINVAL_CYCLES})')
log(f'test 샘플     : {X_test.shape}  (사이클 {TEST_CYCLES})')

results = {}
horizon_results = {}

# ------------------------------------------------------------
# 2) Ridge 모델
# ------------------------------------------------------------
log(f'\n[1/2] Ridge (alpha={RIDGE_ALPHA}, 입력을 1512차원으로 펼쳐서 다중출력 회귀)')
X_train_flat = X_train.reshape(len(X_train), -1)
X_test_flat = X_test.reshape(len(X_test), -1)

ridge = Ridge(alpha=RIDGE_ALPHA).fit(X_train_flat, Y_train)
ridge_pred = ridge.predict(X_test_flat)
horizon_results['Ridge'] = evaluate_multistep('Ridge', Y_test, ridge_pred, results)

# ------------------------------------------------------------
# 3) LSTM 모델
# ------------------------------------------------------------
log(f'\n[2/2] LSTM ({len(LSTM_SEEDS)}개 시드 평균, hidden={LSTM_HIDDEN}, layers={LSTM_LAYERS})')
seed_preds = []
for seed in LSTM_SEEDS:
    m = train_lstm(X_train, Y_train, n_features=len(FEATURE_COLS), horizon=FORECAST_HORIZON, seed=seed)
    seed_preds.append(predict_lstm(m, X_test))
    log(f'  seed={seed} 완료')
lstm_pred = np.mean(seed_preds, axis=0)
horizon_results['LSTM'] = evaluate_multistep('LSTM (10-seed 평균)', Y_test, lstm_pred, results)

# ------------------------------------------------------------
# 3-1) 예측값 저장
# ------------------------------------------------------------
np.savez(
    'ML/results/predictions.npz',
    Y_test=Y_test,
    ridge_pred=ridge_pred,
    lstm_pred=lstm_pred,
    test_dates=test_dates,
)
log('\n[예측값 저장 완료] ML/results/predictions.npz')

# ------------------------------------------------------------
# 4) 결과 비교
# ------------------------------------------------------------
log('\n' + '=' * 70)
log('최종 비교 (test 사이클 9~10, 1~24시간 후 통합)')
log('=' * 70)
for name, m in results.items():
    log(f'{name:20s} RMSE={m["RMSE"]:.4f}  MAE={m["MAE"]:.4f}  R2={m["R2"]:.4f}')

# ------------------------------------------------------------
# 5) 시각화
# ------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
hours = range(1, FORECAST_HORIZON + 1)
axes[0].plot(hours, horizon_results['Ridge'][0], marker='o', label='Ridge', color='tab:blue')
axes[0].plot(hours, horizon_results['LSTM'][0], marker='o', label='LSTM', color='tab:red')
axes[0].set_ylabel('RMSE')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(hours, horizon_results['Ridge'][1], marker='o', label='Ridge', color='tab:blue')
axes[1].plot(hours, horizon_results['LSTM'][1], marker='o', label='LSTM', color='tab:red')
axes[1].set_ylabel('R2')
axes[1].set_xlabel('예측 시점 (몇 시간 후)')
axes[1].legend()
axes[1].grid(alpha=0.3)

axes[0].set_title('예측 시점(horizon)별 성능 비교 — Ridge vs LSTM')

fig.tight_layout()
fig.savefig(f'{OUT_DIR}/multistep_horizon_comparison.png', dpi=150)
plt.close(fig)
log(f'\n[그림 저장] {OUT_DIR}/multistep_horizon_comparison.png')

# 샘플 시점 24시간 예측 궤적 비교
sample_idxs = np.linspace(0, len(X_test) - 1, 4, dtype=int)
fig, axes = plt.subplots(2, 2, figsize=(13, 8))
for ax, idx in zip(axes.flat, sample_idxs):
    ax.plot(hours, Y_test[idx], label='실제', color='black', marker='o', markersize=3)
    ax.plot(hours, ridge_pred[idx], label='Ridge', color='tab:blue', marker='o', markersize=3)
    ax.plot(hours, lstm_pred[idx], label='LSTM', color='tab:red', marker='o', markersize=3)
    ax.set_title(f'예측 시작: {pd.Timestamp(test_dates[idx])}')
    ax.set_xlabel('예측 시점 (시간 후)')
    ax.set_ylabel('비플럭스')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
fig.suptitle('샘플 시점별 24시간 예측 궤적 비교 (실제 vs Ridge vs LSTM)')

fig.tight_layout()
fig.savefig(f'{OUT_DIR}/multistep_sample_forecasts.png', dpi=150)
plt.close(fig)
log(f'[그림 저장] {OUT_DIR}/multistep_sample_forecasts.png')

with open(RESULT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'\n결과 저장: {RESULT_PATH}')
