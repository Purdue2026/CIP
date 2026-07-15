import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

SRC = os.path.join(DATA_DIR, "processed", "dataset_outliers_removed.csv")
DST = os.path.join(DATA_DIR, "processed", "dataset_stage2.csv")
DST_MODEL = os.path.join(DATA_DIR, "processed", "dataset_model_ready.csv")
DS2 = os.path.join(DATA_DIR, "raw", "kwater_recipe06_dataset2.xlsx")

WATER_Q = ["원수 탁도", "원수 TDS", "원수 전기전도도", "원수 pH", "원수 수온"]
OP_COLS = ["비플럭스", "운영차압", "유입압력", "생산량"]  # 운전 관련 컬럼(사이클 내 보간 대상)

# 탁도 35일 장기결측 구간
GAP0 = pd.Timestamp("2021-05-10 08:00:01")
GAP1 = pd.Timestamp("2021-06-14 14:00:01")

MAKE_MODEL_READY = True


def interp_within_cycle(s, cyc):
    out = s.copy()
    for cid, idx in s.groupby(cyc).groups.items():
        out.loc[idx] = s.loc[idx].interpolate("linear", limit_direction="both")
    out[cyc == 0] = np.nan
    return out


def turbidity_splice(df):
    if not os.path.exists(DS2):
        print(f"[splice] dataset2 없음({DS2}) → 탁도 splice 건너뜀, 선형보간으로 대체")
        return

    d2 = pd.read_excel(DS2, sheet_name="RO1")
    d2["Date"] = pd.to_datetime(d2["Date"], errors="coerce")
    t2 = pd.to_numeric(d2["원수 탁도"], errors="coerce")
    t2 = t2.where((t2 > 0) & t2.notna())            # dataset2 자체 결측 제외

    d2_keys = d2["Date"].dt.strftime("%m-%d-%H")
    lut = pd.Series(t2.values, index=d2_keys.values)
    lut = lut[~lut.index.duplicated(keep="first")]

    gap_mask = df["원수 탁도"].isna() & (df["Date"] >= GAP0) & (df["Date"] <= GAP1)

    keys = df.loc[gap_mask, "Date"].dt.strftime("%m-%d-%H")
    spliced = keys.map(lut)
    df.loc[gap_mask, "원수 탁도"] = spliced.values


def main():
    df = pd.read_csv(SRC)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    cyc = df["cycle_id"]

    # 탁도 장기결측
    turbidity_splice(df)

    # 운전 컬럼
    for c in OP_COLS:
        df[c] = interp_within_cycle(df[c], cyc)

    # 수질·기온
    for c in WATER_Q + ["temp"]:
        df[c] = df[c].interpolate("linear", limit_direction="both")

    # 강수량
    df["rain"] = df["rain"].fillna(0.0)

    df.to_csv(DST, index=False, encoding="utf-8-sig")
    print(f"저장: {DST}  ({df.shape[0]}행 × {df.shape[1]}열)")

    if MAKE_MODEL_READY:
        mr = df.copy()
        filled = {}
        for c in OP_COLS:
            n = int(mr[c].isna().sum())
            mr.loc[mr[c].isna(), c] = 0.0
            filled[c] = n
        left = int(mr[OP_COLS].isna().sum().sum())
        mr.to_csv(DST_MODEL, index=False, encoding="utf-8-sig")
        print(f"저장: {DST_MODEL}  (NaN→0 {filled}, 잔여 NaN={left})")


if __name__ == "__main__":
    main()