"""
사이클별 시계열 시각화 — dataset_stage1.csv

1) 전체 개요: 비플럭스·운영차압 두 패널에 세척구간(is_operating=False)을 회색으로 표시하고
   각 사이클 경계에 번호를 붙인 그림 (plots/cycles_overview.png)
2) 사이클별 상세: 사이클마다 9개 변수 전체를 grid subplot으로 그린 그림
   (plots/cycles/cycle_01_vars.png ~ cycle_10_vars.png)
"""
import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = 'EDA/plots'
CYCLE_DIR = os.path.join(OUT_DIR, 'cycles')
os.makedirs(CYCLE_DIR, exist_ok=True)

DATA_PATH = 'data/processed/dataset_stage1.csv'
COLUMNS = [
    '운영차압', '비플럭스', '원수 수온', '원수 탁도',
    '원수 TDS', '원수 전기전도도', '원수 pH', '유입압력', '생산량',
]

df = pd.read_csv(DATA_PATH, parse_dates=['Date'])

# ============================================================
# 1) 전체 개요 — 비플럭스/운영차압 + 세척구간 음영 + 사이클 번호
# ============================================================
fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

for ax, col, color in zip(axes, ['비플럭스', '운영차압'], ['tab:blue', 'tab:red']):
    ax.plot(df['Date'], df[col], linewidth=0.7, color=color)
    ax.set_ylabel(col)
    ax.grid(alpha=0.3)

# 세척구간(is_operating=False) 음영 표시
not_op = ~df['is_operating'].to_numpy()
n = len(df)
i = 0
while i < n:
    if not_op[i]:
        j = i
        while j < n and not_op[j]:
            j += 1
        for ax in axes:
            ax.axvspan(df['Date'].iloc[i], df['Date'].iloc[j - 1], color='gray', alpha=0.25)
        i = j
    else:
        i += 1

# 사이클 경계에 빨간 세로선 표시 + 번호 라벨 (겹침 방지를 위해 y위치를 번갈아 배치)
cycle_groups = list(df[df['cycle_id'] > 0].groupby('cycle_id'))
for idx, (cid, g) in enumerate(cycle_groups):
    start_date = g['Date'].iloc[0]
    end_date = g['Date'].iloc[-1]
    for ax in axes:
        ax.axvline(start_date, color='red', linestyle='--', linewidth=1, alpha=0.8)
        ax.axvline(end_date, color='red', linestyle='--', linewidth=1, alpha=0.8)
    y_frac = 0.95 if idx % 2 == 0 else 0.80
    ylo, yhi = axes[0].get_ylim()
    axes[0].text(start_date, ylo + (yhi - ylo) * y_frac, f' cycle {cid}',
                 ha='left', va='top', fontsize=9, color='darkred')

axes[0].set_title('전체 개요 — 비플럭스/운영차압 (회색=세척/장기결측 구간, 빨간 세로선=사이클 경계)')
axes[-1].set_xlabel('Date')
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'cycles_overview.png'), dpi=150)
plt.close(fig)
print(f'저장: {OUT_DIR}/cycles_overview.png')

# ============================================================
# 2) 사이클별 상세 — 사이클마다 9개 변수 grid subplot
# ============================================================
cycle_ids = sorted(df.loc[df['cycle_id'] > 0, 'cycle_id'].unique())
for cid in cycle_ids:
    g = df[df['cycle_id'] == cid]
    d0, d1 = g['Date'].iloc[0], g['Date'].iloc[-1]

    fig, axes = plt.subplots(len(COLUMNS), 1, figsize=(12, 2.2 * len(COLUMNS)), sharex=True)
    for ax, col in zip(axes, COLUMNS):
        ax.plot(g['Date'], g[col], linewidth=0.7, color='tab:blue')
        ax.set_ylabel(col, fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_title(f'Cycle {cid}  ({d0.date()} ~ {d1.date()}, n={len(g)}시간)')
    axes[-1].set_xlabel('Date')
    fig.tight_layout()
    fname = f'cycle_{cid:02d}_vars.png'
    fig.savefig(os.path.join(CYCLE_DIR, fname), dpi=150)
    plt.close(fig)
    print(f'저장: {CYCLE_DIR}/{fname}')

print(f'\n총 {len(cycle_ids)}개 사이클 그림 완료.')
