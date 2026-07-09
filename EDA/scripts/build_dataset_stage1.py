"""
1차 데이터셋 생성
- 운전 사이클 정의(cycle_id/is_operating)
- 기상데이터(rain/temp) 병합

결과물 : dataset_stage1.csv
"""
import numpy as np
import pandas as pd
import os

RAW_PATH = 'data/raw/kwater_recipe06_dataset1.xlsx'
RAIN_SRC = 'data/raw/강수량(티센다각).csv'
TEMP_SRC = 'data/raw/기온_스플라인보간.csv'
OUT_PATH = 'data/processed/dataset_stage1.csv'
RESULT_PATH = 'EDA/results/stage1_pipeline_results.txt'

COLUMNS = [
    '운영차압', '비플럭스', '원수 수온', '원수 탁도',
    '원수 TDS', '원수 전기전도도', '원수 pH', '유입압력', '생산량',
]

GAP_HOURS = 20
PCT_THRESHOLD = 0.05    # 

lines = []


def log(msg=''):
    print(msg)
    lines.append(str(msg))


def detect_cleaning_cycles(flux, dp, absorb_hours=4, gap_hours=GAP_HOURS, pct_threshold=PCT_THRESHOLD, n_median=10):
    """
    사이클 정의 구간 - 사이클 총 10개
    """
    n = len(flux)
    is_na = flux.isna().to_numpy()

    absorbed = is_na.copy()
    i = 0
    while i < n:
        if not absorbed[i]:
            j = i
            while j < n and not absorbed[j]:
                j += 1
            run_len = j - i
            prev_missing = i > 0 and absorbed[i - 1]
            next_missing = j < n and absorbed[j]
            if run_len <= absorb_hours and prev_missing and next_missing:
                absorbed[i:j] = True
            i = j
        else:
            i += 1

    gaps = []
    i = 0
    while i < n:
        if absorbed[i]:
            j = i
            while j < n and absorbed[j]:
                j += 1
            if (j - i) >= gap_hours:
                gaps.append((i, j))
            i = j
        else:
            i += 1

    flux_vals = flux.to_numpy()
    dp_vals = dp.to_numpy()
    cleaning_gap_mask = np.zeros(n, dtype=bool)
    gap_info = []
    for (gi, gj) in gaps:
        before = flux_vals[max(0, gi - n_median):gi]
        after = flux_vals[gj:gj + n_median]
        before_dp = dp_vals[max(0, gi - n_median):gi]
        after_dp = dp_vals[gj:gj + n_median]
        before = before[~np.isnan(before)]
        after = after[~np.isnan(after)]
        before_dp = before_dp[~np.isnan(before_dp)]
        after_dp = after_dp[~np.isnan(after_dp)]
        flux_pct = dp_pct = np.nan
        if len(before) > 0 and len(after) > 0:
            flux_before_med, flux_after_med = np.median(before), np.median(after)
            flux_pct = (flux_after_med - flux_before_med) / flux_before_med if flux_before_med else np.nan
        if len(before_dp) > 0 and len(after_dp) > 0:
            dp_before_med, dp_after_med = np.median(before_dp), np.median(after_dp)
            dp_pct = (dp_after_med - dp_before_med) / dp_before_med if dp_before_med else np.nan
        is_cleaning = (not np.isnan(flux_pct) and flux_pct >= pct_threshold) or \
                      (not np.isnan(dp_pct) and dp_pct <= -pct_threshold)
        if is_cleaning:
            cleaning_gap_mask[gi:gj] = True
        gap_info.append({
            'start_idx': gi, 'end_idx': gj, 'length_h': gj - gi,
            'flux_pct_change': flux_pct, 'dp_pct_change': dp_pct, 'is_cleaning': is_cleaning,
        })

    any_gap_mask = np.zeros(n, dtype=bool)
    for (gi, gj) in gaps:
        any_gap_mask[gi:gj] = True

    cycle_id = np.zeros(n, dtype=int)
    current_cycle = 1
    prev_in_cleaning = False
    for k in range(n):
        if cleaning_gap_mask[k]:
            cycle_id[k] = 0
            prev_in_cleaning = True
        else:
            if prev_in_cleaning:
                current_cycle += 1
            cycle_id[k] = current_cycle
            prev_in_cleaning = False

    return any_gap_mask, cleaning_gap_mask, cycle_id, gap_info


log('=' * 70)
log('1차 데이터셋 생성 — 이상치/결측치 처리 없이 운전 사이클 정의 + 기상데이터 병합만 수행')
log('=' * 70)

# ======================================
# 1. 원본 데이터 로드
# ======================================
df = pd.read_excel(RAW_PATH, sheet_name='RO1')
df['Date'] = pd.to_datetime(df['Date'])

# 숫자 아닌 값은 NaN 처리
df[COLUMNS] = df[COLUMNS].apply(pd.to_numeric, errors='coerce')

# 시간순 정렬 + 중복시각 제거
df = (df.sort_values('Date')
        .drop_duplicates('Date')
        .set_index('Date'))

log(f'1) dataset1(2021년) 로드: {len(df)}행 ({df.index.min()} ~ {df.index.max()}) — 원본 값 그대로(이상치 미제거)')
for col in COLUMNS:
    log(f'   {col}: 원본 결측 {df[col].isna().sum()}개')

# ======================================
# 2) 운전 사이클 정의
# ======================================
# return : 결측 구간 마스크, 세척 구간 마스크, 각 행의 사이클 번호, 구간별 상세정보
any_gap_mask, cleaning_gap_mask, cycle_id, gap_info = detect_cleaning_cycles(df['비플럭스'], df['운영차압'])

df['is_operating'] = ~any_gap_mask
df['cycle_id'] = cycle_id
n_cleaning = sum(g['is_cleaning'] for g in gap_info)
n_cycles = df.loc[df['cycle_id'] > 0, 'cycle_id'].nunique()

log(f'\n2) 운전 사이클 정의 (비플럭스 {PCT_THRESHOLD:.0%}↑ OR 운영차압 {PCT_THRESHOLD:.0%}↓ 중 하나 = 세척)')
log(f'   {GAP_HOURS}시간 + 결측 후보 {len(gap_info)}개 중 세척 판정 {n_cleaning}개 -> 운전 사이클 {n_cycles}개')

# ======================================
# 2-1) 마지막 사이클 잘라내기 (12월말)
# ======================================
# cycle_id는 항상 "마지막 세척 뒤에 이어지는" 구간이라, 마지막 후보 gap이 세척인지 여부와는 무관하게
# 마지막 사이클 자체가 다른 사이클보다 훨씬 짧으면(=세척이 아니라 연말에 데이터가 그냥 끊긴 조각) 제외한다.
cycle_durations = df.loc[df['cycle_id'] > 0].groupby('cycle_id').size()
last_cid = int(cycle_id[-1])
if last_cid > 0 and len(cycle_durations) > 1:
    median_dur = cycle_durations.drop(last_cid).median()
    last_dur = cycle_durations[last_cid]
    if last_dur < 0.2 * median_dur:
        df.loc[df['cycle_id'] == last_cid, 'cycle_id'] = 0
        n_cycles = df.loc[df['cycle_id'] > 0, 'cycle_id'].nunique()
        log(f'   -> 마지막 cycle {last_cid}는 세척이 아니라 연말 데이터 끝(트레일링 {last_dur}시간, '
            f'중앙값 {median_dur:.0f}h의 20% 미만)이라 제외 -> 최종 운전 사이클 {n_cycles}개')

# ======================================
# 3) 기상데이터 병합 (시간 단위로 내림해서 병합)
# 일시를 datetime → floor('h')로 분/초 버리고 시간 단위로 맞춤
# ======================================

def load_weather(path, value_col, new_name):
    w = pd.read_csv(path)
    w.columns = w.columns.str.strip()
    w['Date_hour'] = pd.to_datetime(w['일시']).dt.floor('h')
    return w.rename(columns={value_col: new_name})[['Date_hour', new_name]]

rain_df = load_weather(RAIN_SRC, '강수량(mm)', 'rain')
temp_df = load_weather(TEMP_SRC, 'temp_spline', 'temp')

df = df.reset_index()
df['Date_hour'] = df['Date'].dt.floor('h')
df = (df.merge(rain_df, on='Date_hour', how='left')
        .merge(temp_df, on='Date_hour', how='left')
        .drop(columns='Date_hour'))

log(f'\n3) 기상데이터 병합 (원본 그대로, 결측치 처리 안 함): '
    f'rain 결측 {df["rain"].isna().sum()}개, temp 결측 {df["temp"].isna().sum()}개 (여기서 채우지 않음)')

os.makedirs('data/processed', exist_ok=True)
os.makedirs('EDA/results', exist_ok=True)
df.to_csv(OUT_PATH, index=False)
log(f'\n저장 완료: {OUT_PATH} ({len(df)}행, {len(df.columns)}컬럼)')
log(f'컬럼: {list(df.columns)}')
log('\n※ 이 파일은 이상치 제거/보간이 전혀 안 된 1차본입니다. '
    '9개 센서 컬럼의 물리한계값·Z-score 이상치 처리와 결측치 보간은 다음 단계에서 별도로 진행합니다.')

with open(RESULT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'\n결과 텍스트 저장: {os.path.abspath(RESULT_PATH)}')
