import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUT_DIR = os.path.join(BASE_DIR, "plots")
os.makedirs(OUT_DIR, exist_ok=True)

COLS = ["비플럭스", "운영차압"]

stage1 = pd.read_csv(os.path.join(DATA_DIR, "dataset_stage1.csv"), parse_dates=["Date"])
outliers_removed = pd.read_csv(os.path.join(DATA_DIR, "dataset_outliers_removed.csv"), parse_dates=["Date"])
stage2 = pd.read_csv(os.path.join(DATA_DIR, "dataset_stage2.csv"), parse_dates=["Date"])

fig, axes = plt.subplots(len(COLS), 2, figsize=(16, 4 * len(COLS)), sharex=True)

for row, col in enumerate(COLS):
    ax_outlier, ax_fill = axes[row]

    ax_outlier.plot(stage1["Date"], stage1[col], color="gray", linewidth=0.7, label="처리 전 (stage1)")
    ax_outlier.plot(outliers_removed["Date"], outliers_removed[col], color="tab:red", linewidth=0.7, label="처리 후 (이상치 제거)")
    ax_outlier.set_ylabel(col)
    ax_outlier.set_title(f"{col} — 이상치 처리 전/후")
    ax_outlier.legend(fontsize=8)
    ax_outlier.grid(alpha=0.3)

    ax_fill.plot(outliers_removed["Date"], outliers_removed[col], color="gray", linewidth=0.7, label="처리 전 (이상치 제거)")
    ax_fill.plot(stage2["Date"], stage2[col], color="tab:blue", linewidth=0.7, label="처리 후 (결측치 보간, stage2)")
    ax_fill.set_title(f"{col} — 결측치 처리 전/후")
    ax_fill.legend(fontsize=8)
    ax_fill.grid(alpha=0.3)

axes[-1][0].set_xlabel("Date")
axes[-1][1].set_xlabel("Date")
fig.tight_layout()
out_path = os.path.join(OUT_DIR, "before_after.png")
fig.savefig(out_path, dpi=150)
plt.close(fig)
print(f"저장: {out_path}")
