import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 한글 폰트 설정 (macOS)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = 'EDA/plots'
os.makedirs(OUT_DIR, exist_ok=True)

# 2021년(dataset1)만 사용
RAW_PATH = 'data/raw/kwater_recipe06_dataset1.xlsx'

COLUMNS = [
    '운영차압', '비플럭스', '원수 수온', '원수 탁도',
    '원수 TDS', '원수 전기전도도', '원수 pH', '유입압력', '생산량',
]

df1 = pd.read_excel(RAW_PATH, sheet_name='RO1')
df1['Date'] = pd.to_datetime(df1['Date'])
for col in COLUMNS:
    df1[col] = pd.to_numeric(df1[col], errors='coerce')

# 1) 컬럼별 시계열 플롯
for col in COLUMNS:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df1['Date'], df1[col], linewidth=0.8, color='tab:blue')
    ax.set_title(f'RO1 - {col} (2021)')
    ax.set_xlabel('Date')
    ax.set_ylabel(col)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, f'timeseries_{col}.png'), dpi=150)
    plt.close(fig)

# 2) 컬럼별 분포 히스토그램
for col in COLUMNS:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df1[col].dropna(), bins=50, alpha=0.7, color='tab:blue')
    ax.set_title(f'RO1 - {col} 분포 (2021)')
    ax.set_xlabel(col)
    ax.set_ylabel('빈도')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, f'hist_{col}.png'), dpi=150)
    plt.close(fig)

# 3) 전체 컬럼 오버뷰 (subplot grid)
fig, axes = plt.subplots(len(COLUMNS), 1, figsize=(12, 3 * len(COLUMNS)), sharex=True)
for ax, col in zip(axes, COLUMNS):
    ax.plot(df1['Date'], df1[col], linewidth=0.6, color='tab:blue')
    ax.set_ylabel(col)
    ax.grid(alpha=0.3)
axes[0].set_title('RO1 dataset1 (2021) 전체 컬럼 개요')
axes[-1].set_xlabel('Date')
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'overview_dataset1.png'), dpi=150)
plt.close(fig)

print(f"저장 완료: {os.path.abspath(OUT_DIR)}")
print(os.listdir(OUT_DIR))
