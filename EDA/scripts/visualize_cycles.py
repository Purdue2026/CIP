"""
사이클별 시계열 시각화

- 비플럭스·운영차압 두 패널에 세척구간(is_operating=False)을 회색으로 표시하고
- 각 사이클 경계에 번호를 붙인 그림 (plots/cycles_overview.png)
"""
import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = 'EDA/plots'
os.makedirs(OUT_DIR, exist_ok=True)

DATA_PATH = 'data/processed/dataset_stage1.csv'
df = pd.read_csv(DATA_PATH, parse_dates=['Date'])

fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

for ax, col, color in zip(axes, ['비플럭스', '운영차압'], ['tab:blue', 'tab:red']):
    ax.plot(df['Date'], df[col], linewidth=0.7, color=color)
    ax.set_ylabel(col)
    ax.grid(alpha=0.3)

# 세척/장기결측 구간(is_operating=False) 음영 표시
is_stopped = ~df['is_operating'].to_numpy()
n = len(df)
i = 0
while i < n:
    if is_stopped[i]:
        j = i
        while j < n and is_stopped[j]:
            j += 1
        for ax in axes:
            ax.axvspan(df['Date'].iloc[i], df['Date'].iloc[j - 1], color='gray', alpha=0.25)
        i = j
    else:
        i += 1

# 사이클 경계에 빨간 세로선 + 번호 라벨
cycle_groups = list(df[df['cycle_id'] > 0].groupby('cycle_id'))
ylo, yhi = axes[0].get_ylim()
for idx, (cid, grp) in enumerate(cycle_groups):
    start_date = grp['Date'].iloc[0]
    end_date = grp['Date'].iloc[-1]

    for ax in axes:
        ax.axvline(start_date, color='red', linestyle='--', linewidth=1, alpha=0.8)
        ax.axvline(end_date, color='red', linestyle='--', linewidth=1, alpha=0.8)
    y_frac = 0.95 if idx % 2 == 0 else 0.80
    axes[0].text(start_date, ylo + (yhi - ylo) * y_frac, f' cycle {cid}',
                 ha='left', va='top', fontsize=9, color='darkred')

axes[0].set_title('전체 개요 — 비플럭스/운영차압 (회색=세척/장기결측 구간, 빨간 세로선=사이클 경계)')
axes[-1].set_xlabel('Date')
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'cycles_overview.png'), dpi=150)
plt.close(fig)
print(f'저장: {OUT_DIR}/cycles_overview.png')