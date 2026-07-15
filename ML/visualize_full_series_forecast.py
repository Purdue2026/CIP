import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

DATA_PATH = 'data/processed/dataset_stage2.csv'
PRED_PATH = 'ML/results/predictions.npz'
OUT_DIR = 'ML/plots'

TARGET_COL = '비플럭스'
TEST_CYCLES = [9, 10]
FORECAST_HORIZON = 24
CLEANING_DROP_PCT = 0.10  # 원래 세척 기준: 사이클 시작 대비 10% 감소


def build_full_series(Y_true, pred, dates, cycle_ids, horizon):
    full_actual, full_pred, full_dates, full_cids = [], [], [], []
    order = np.argsort(dates)
    dates_sorted = dates[order]
    Y_true_sorted = Y_true[order]
    pred_sorted = pred[order]
    cid_sorted = cycle_ids[order]

    for cid in np.unique(cid_sorted):
        mask = cid_sorted == cid
        idxs = np.where(mask)[0]
        starts = list(range(0, len(idxs), horizon))
        if starts[-1] != len(idxs) - 1:
            starts.append(len(idxs) - 1)
        for start in starts:
            i = idxs[start]
            full_actual.append(Y_true_sorted[i])
            full_pred.append(pred_sorted[i])
            base_date = pd.Timestamp(dates_sorted[i])
            full_dates.extend([base_date + pd.Timedelta(hours=h) for h in range(horizon)])
            full_cids.extend([cid] * horizon)

    full_actual = np.concatenate(full_actual)
    full_pred = np.concatenate(full_pred)
    full_dates = np.array(full_dates)
    full_cids = np.array(full_cids)

    order2 = np.argsort(full_dates, kind='stable')
    full_dates, full_actual, full_pred, full_cids = (
        full_dates[order2], full_actual[order2], full_pred[order2], full_cids[order2])
    _, unique_idx = np.unique(full_dates, return_index=True)
    return (full_actual[unique_idx], full_pred[unique_idx],
            full_dates[unique_idx], full_cids[unique_idx])

# ------------------------------------------------------------
# 1) 예측값 로드, 원본 데이터 로드
# ------------------------------------------------------------
pred_data = np.load(PRED_PATH)
Y_test = pred_data['Y_test']
ridge_pred = pred_data['ridge_pred']
lstm_pred = pred_data['lstm_pred']
test_dates = pred_data['test_dates']

df = pd.read_csv(DATA_PATH, parse_dates=['Date'])
df = df[df['is_operating']].reset_index(drop=True)
test_df = df[df['cycle_id'].isin(TEST_CYCLES)].reset_index(drop=True)

date_to_cycle = dict(zip(test_df['Date'], test_df['cycle_id']))
window_cycle_ids = np.array([date_to_cycle[pd.Timestamp(d)] for d in test_dates])

# ------------------------------------------------------------
# 2) 전체 구간 연결
# ------------------------------------------------------------
full_actual, full_ridge, full_dates, full_cids = build_full_series(
    Y_test, ridge_pred, test_dates, window_cycle_ids, FORECAST_HORIZON)
_, full_lstm, _, _ = build_full_series(
    Y_test, lstm_pred, test_dates, window_cycle_ids, FORECAST_HORIZON)

# ------------------------------------------------------------
# 3) 사이클 시작 대비 10% 감소 시점 = 원래 세척 기준 정의
# ------------------------------------------------------------
cycle_start_val = {
    cid: g.sort_values('Date')[TARGET_COL].iloc[0]
    for cid, g in test_df.groupby('cycle_id')
}
mark_dates, mark_vals = [], []
for cid in np.unique(full_cids):
    idxs = np.where(full_cids == cid)[0]
    ref = cycle_start_val[cid]
    below = np.where(full_actual[idxs] <= ref * (1 - CLEANING_DROP_PCT))[0]
    if below.size > 0:
        i = idxs[below[0]]
        mark_dates.append(full_dates[i])
        mark_vals.append(full_actual[i])

# ------------------------------------------------------------
# 4) 시각화
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 5))
ax.plot(full_dates, full_actual, label='실제', color='black', linewidth=1.2)
ax.plot(full_dates, full_ridge, label='Ridge', color='tab:blue', linewidth=1, alpha=0.8)
ax.plot(full_dates, full_lstm, label='LSTM (10-seed 평균)', color='tab:red', linewidth=1, alpha=0.8)
ax.scatter(mark_dates, mark_vals, marker='o', s=60, color='crimson', zorder=5,
           label='세척 시점 (사이클 시작 대비 10% 감소)')
ax.set_xlabel('시각')
ax.set_ylabel('비플럭스')
ax.set_title('test 사이클(9~10) 전체 구간 예측 비교 (24시간 단위로 이어붙임, 실제 vs Ridge vs LSTM)')
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(f'{OUT_DIR}/multistep_full_series_forecast.png', dpi=150)
plt.close(fig)
print(f'[그림 저장] {OUT_DIR}/multistep_full_series_forecast.png')
