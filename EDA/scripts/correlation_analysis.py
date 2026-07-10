import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = 'EDA/plots'
os.makedirs(OUT_DIR, exist_ok=True)
RESULT_PATH = 'EDA/logs/eda_correlation_results.txt'

COLUMNS_SIMPLE = [
    '비플럭스', '운영차압', '원수 탁도', '원수 pH', '생산량',
    'rain', 'temp', '원수 수온', '원수 TDS', '유입압력',
]

lines = []


def log(msg=''):
    print(msg)
    lines.append(str(msg))


def corr_block(df, cols, label):
    corr = df[cols].corr(method='pearson')
    log(f'\n=== {label}: Pearson 상관계수 행렬 ===')
    log(corr.round(3).to_string())

    # 절댓값 0.5 이상 강한 상관 쌍만 추출
    log(f'\n--- {label}: |r| >= 0.5 강한 상관 쌍 ---')
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            if pd.notna(r) and abs(r) >= 0.5:
                pairs.append((a, b, r))
    pairs.sort(key=lambda x: -abs(x[2]))
    if pairs:
        for a, b, r in pairs:
            log(f'  {a} vs {b}: r={r:.3f}')
    else:
        log('  (없음)')

    fig, ax = plt.subplots(figsize=(1 + 0.9 * len(cols), 1 + 0.8 * len(cols)))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1,
                square=True, ax=ax, cbar_kws={'shrink': 0.8})
    ax.set_title(f'{label} - 상관계수 히트맵')
    fig.tight_layout()
    fname = f'corr_heatmap_{label}.png'
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=150)
    plt.close(fig)
    log(f'  [그림 저장] {OUT_DIR}/{fname}')
    return corr


log('=' * 70)
log('EDA - 변수 간 상관관계 분석 결과')
log('=' * 70)

# 1) dataset_stage1.csv (이상치/결측치 처리 전, 사이클+기상만 붙인 1차본, 2021년 전체)
log('\n\n' + '=' * 70)
log('dataset_stage1.csv (1차본 — 이상치/결측치 처리 없음, cycle_id/rain/temp만 추가, 2021년 전체)')
log('=' * 70)
df_i = pd.read_csv('data/processed/dataset_stage1.csv')
df_i['Date'] = pd.to_datetime(df_i['Date'])
corr_i = corr_block(df_i, COLUMNS_SIMPLE, 'stage1')

# 2) 비플럭스 중심 - 시차(lag) 상관 분석 (기상/수질 변수가 비플럭스에 미치는 지연 영향)
log('\n\n' + '=' * 70)
log('비플럭스 vs 주요 변수 - 시차(lag) 교차상관 분석 (0~72시간)')
log('=' * 70)
lag_targets = ['rain', 'temp', '원수 수온', '원수 TDS', '원수 탁도', '원수 pH', '유입압력', '생산량']
max_lag = 72
lag_summary = []
for col in lag_targets:
    series_x = df_i[col]
    series_y = df_i['비플럭스']
    best_r, best_lag = 0, 0
    for lag in range(0, max_lag + 1):
        r = series_x.shift(lag).corr(series_y)
        if pd.notna(r) and abs(r) > abs(best_r):
            best_r, best_lag = r, lag
    lag_summary.append((col, best_lag, best_r))
    log(f'  {col}: 최대상관 |r|={best_r:.3f} at lag={best_lag}h (rain/temp/수질 -> 비플럭스, {best_lag}시간 후행)')

# lag-correlation curve plot
fig, ax = plt.subplots(figsize=(9, 5))

for col in ['rain', 'temp', '원수 수온', '원수 TDS']:
    rs = [df_i[col].shift(lag).corr(df_i['비플럭스']) for lag in range(0, max_lag + 1)]
    ax.plot(range(0, max_lag + 1), rs, label=col, linewidth=1.2)

ax.axhline(0, color='gray', linewidth=0.8)
ax.set_xlabel('Lag (hours, X가 Y보다 lag시간 선행)')
ax.set_ylabel('Pearson r (vs 비플럭스)')
ax.set_title('비플럭스에 대한 시차 교차상관 (기상/수질 변수)')
ax.legend()
fig.tight_layout()

fig.savefig(os.path.join(OUT_DIR, 'lag_correlation_비플럭스.png'), dpi=150)
plt.close(fig)
log(f'\n  [그림 저장] {OUT_DIR}/lag_correlation_비플럭스.png')

# 3) 핵심 산점도 (비플럭스, 운영차압 vs 원수 수질/기상)
log('\n\n' + '=' * 70)
log('핵심 산점도 저장 (비플럭스/운영차압 vs 원수 수질·기상 변수)')
log('=' * 70)

scatter_targets = ['원수 수온', '원수 탁도', '원수 TDS', '원수 pH', 'rain', 'temp']

for y_col in ['비플럭스', '운영차압']:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))

    for ax, x_col in zip(axes.flat, scatter_targets):
        r = df_i[x_col].corr(df_i[y_col])
        ax.scatter(df_i[x_col], df_i[y_col], s=3, alpha=0.3)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f'r={r:.3f}'
        )
    fig.suptitle(f'{y_col} vs 원수 수질·기상 변수 (산점도)')
    fig.tight_layout()
    fname = f'scatter_{y_col}_vs_water_weather.png'

    fig.savefig(os.path.join(OUT_DIR, fname), dpi=150)
    plt.close(fig)
    log(f'  [그림 저장] {OUT_DIR}/{fname}')

with open(RESULT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'\n결과 텍스트 저장 완료: {os.path.abspath(RESULT_PATH)}')
