# EDA (Exploratory Data Analysis)

Summary statistics, data quality notes, and correlation/cycle analysis for the data in `data/`.
For the data itself (files, columns), see [`../data/README.md`](../data/README.md).

> This analysis uses `dataset_stage1.csv`, which has **no outlier or missing-value cleanup yet** — it only adds operating cycles (`cycle_id`/`is_operating`) and weather data (`rain`/`temp`). That cleanup happens separately in `dataset_stage2.csv`.

```
EDA/
├── README.md
├── scripts/    # analysis scripts (run from project root)
├── logs/       # text results
└── plots/      # charts (png)
```

---

## Basic Stats (Dataset1, full year 2021, 8,760 rows)

| Column | Mean | Min | Max | Std Dev | Missing % |
|--------|------|-----|-----|---------|-----------|
| 운영차압 (bar) | 3.81 | 1.88 | 6.99 | 0.70 | 26.9% |
| 비플럭스 (LMH/bar) | 4.74 | -0.00 | 7.34 | 0.70 | 25.2% |
| 원수 수온 (°C) | 15.2 | 0.0 | 28.1 | 7.86 | 0.1% |
| 원수 탁도 (NTU) | 0.47 | 0.00 | 8.03 | 0.28 | 0.1% |
| 원수 TDS (mg/L) | 410.9 | 0.0 | 609.2 | 110.0 | 0.1% |
| 원수 전기전도도 (μS/cm) | 684.8 | 0.0 | 1015.3 | 183.3 | 0.1% |
| 원수 pH | 6.90 | 0.00 | 7.18 | 0.64 | 0.1% |
| 유입압력 (bar) | 10.4 | 6.34 | 19.0 | 2.55 | 25.6% |
| 생산량 (m³/h) | 791.8 | 0.0 | 905.9 | 59.4 | 25.6% |

---

## Analysis Scripts

| What it does | Script | Result | Charts |
|---|---|---|---|
| Build stage-1 dataset (no cleanup yet) — adds operating cycles + weather data | `scripts/build_dataset_stage1.py` | `logs/stage1_pipeline_results.txt` → `data/processed/dataset_stage1.csv` | `plots/cycles_overview.png` |
| Time series & distribution charts (raw dataset1, 2021) | `scripts/visualize_ro1.py` | - | `plots/timeseries_*.png`, `plots/hist_*.png`, `plots/overview_dataset1.png` |
| Time series by cycle (10 cycles, from dataset_stage1.csv) | `scripts/visualize_cycles.py` | - | `plots/cycles_overview.png` |
| Bar chart of cycle durations | `scripts/visualize_cycle_duration.py` | - | `plots/cycle_duration.png` |
| Correlation, time-lag, and scatter analysis (dataset_stage1.csv) | `scripts/correlation_analysis.py` | `logs/eda_correlation_results.txt` | `plots/corr_heatmap_stage1.png`, `plots/lag_correlation_비플럭스.png`, `plots/scatter_*.png` |

Run all scripts from the project root, e.g. `./venv/bin/python3 EDA/scripts/build_dataset_stage1.py`.
