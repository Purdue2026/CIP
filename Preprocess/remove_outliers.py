import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

SRC = os.path.join(DATA_DIR, "processed", "dataset_stage1.csv")
DST = os.path.join(DATA_DIR, "processed", "dataset_outliers_removed.csv")

WATER_Q = ["원수 탁도", "원수 TDS", "원수 전기전도도", "원수 pH", "원수 수온"]
ZERO_NAN = WATER_Q + ["생산량", "운영차압", "유입압력"]  # 0 → NaN(결측)
SPIKE_COL = ["비플럭스", "운영차압", "유입압력"]      # rolling z-score
DIP_COL = ["원수 TDS", "원수 전기전도도"]            # 급강하 dip
BIFLUX_FLOOR = 2.46                                # 비플럭스 물리. 하한

# 자동 탐지(dip_mask)가 못 잡는 개별 이상 구간 수동 지정
MANUAL_NAN_RANGES = [
    ("원수 TDS", "2021-05-02 05:00:01", "2021-05-03 14:00:01"),
    ("원수 전기전도도", "2021-05-02 05:00:01", "2021-05-03 14:00:01"),
    ("생산량", "2021-06-07 00:00:01", "2021-06-07 23:00:01"), 
]


def rolling_z_mask(s, window=24, thr=3.0):
    mean = s.rolling(window, center=True, min_periods=window // 2).mean()
    std = s.rolling(window, center=True, min_periods=window // 2).std()
    std = std.replace(0, np.nan)
    z = (s - mean) / std
    return (z.abs() > thr).fillna(False)

def dip_mask(s, window=25, k=6.0, dilate=3):
    med = s.rolling(window, center=True, min_periods=window // 2).median()
    resid = s - med
    scale = (resid.quantile(0.99) - resid.quantile(0.01)) / 2
    thr = k * scale
    mask = (resid.abs() > thr).fillna(False)

    if dilate > 0:
        mask = mask.rolling(2 * dilate + 1, center=True, min_periods=1).max() > 0
    return mask & s.notna()


def main():
    df = pd.read_csv(SRC)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    op = df["is_operating"].astype(bool)
    orig = df.copy()

    # 1) 결측 복원: 0 → NaN
    for c in ZERO_NAN:
        df.loc[df[c] == 0, c] = np.nan

    # 2) 비플럭스 물리적으로 불가능한 값 → NaN
    m = (df["비플럭스"] <= BIFLUX_FLOOR) & op
    df.loc[m, "비플럭스"] = np.nan

    # 3) 고립 스파이크: rolling z-score
    for c in SPIKE_COL:
        s = df[c].where(op)
        mask = rolling_z_mask(s) & df[c].notna()
        df.loc[mask, c] = np.nan

    # 3b) 급강하 dip: '센서 블랙아웃 직후 복귀 오류' 제거
    tds_gap = (orig["원수 TDS"] == 0) | orig["원수 TDS"].isna()
    near_gap = tds_gap.rolling(9, center=True, min_periods=1).max().astype(bool)
    for c in DIP_COL:
        raw = dip_mask(df[c]) & df[c].notna()
        mask = raw & near_gap
        df.loc[mask, c] = np.nan

    # 3c) 수동 지정 이상 구간 → NaN
    for col, start, end in MANUAL_NAN_RANGES:
        mask = (df["Date"] >= start) & (df["Date"] <= end)
        df.loc[mask, col] = np.nan

    df.to_csv(DST, index=False, encoding="utf-8-sig")
    print(f"저장: {DST}  ({df.shape[0]}행 × {df.shape[1]}열)")


if __name__ == "__main__":
    main()
