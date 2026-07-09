import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = 'EDA/plots'
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv('data/processed/dataset_stage1.csv', parse_dates=['Date'])

durations = df[df['cycle_id'] > 0].groupby('cycle_id').size()

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(durations.index.astype(str), durations.values, color='tab:blue')
ax.set_xlabel('cycle_id')
ax.set_ylabel('지속 시간 (시간)')
ax.set_title(f'사이클별 지속 시간 (총 {len(durations)}개)')
for i, v in enumerate(durations.values):
    ax.text(i, v + 10, str(v), ha='center', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'cycle_duration.png'), dpi=150)
plt.close(fig)

print('저장:', os.path.join(OUT_DIR, 'cycle_duration.png'))
print(durations)
