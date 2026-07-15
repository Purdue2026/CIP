# Data

Hourly operating data from a water treatment plant (RO membrane process)

---

## Files

| File | Location | Period | Rows | Notes |
|------|----------|--------|------|-------|
| `kwater_recipe06_dataset1.xlsx` | `raw/` | 2021-01-01 ~ 2021-12-31 | 8,760 rows (RO1 sheet) | Raw data |
| `kwater_recipe06_dataset2.xlsx` | `raw/` | 2022-01-01 ~ 2022-06-30 | 4,344 rows (RO1 sheet) | Raw data |
| `강수량(티센다각).csv` | `raw/` | 2021-01-01 ~ 2022-07-05 | 13,200 rows | Raw weather (rainfall), source of `rain` in `dataset_stage1.csv` |
| `기온_스플라인보간.csv` | `raw/` | 2021-01-01 ~ 2022-12-31 | 17,467 rows | Raw weather (temperature), source of `temp` in `dataset_stage1.csv` |
| `dataset_stage1.csv` | `processed/` | 2021-01-01 ~ 2021-12-31 | 8,760 rows | **Step 1** — before outlier/missing-value cleanup, just adds operating cycles + weather data |
| `dataset_stage2.csv` | `processed/` | 2021-01-01 ~ 2021-12-31 | 8,760 rows | **Step 2** — outliers removed, missing values filled in. Used by `ML/model_comparison.py` |

- Data is recorded every **1 hour** (timestamp format: `YYYY-MM-DD HH:00:01`)
- **Only 2021 data (dataset1) is used.** dataset2 (first half of 2022) is excluded from analysis

---

## About `dataset_stage1.csv`
Script: [`../EDA/scripts/build_dataset_stage1.py`](../EDA/scripts/build_dataset_stage1.py)

- No outlier or missing-value cleanup yet
- Adds operating cycle labels (`cycle_id`, `is_operating`)
- Adds weather data from `data/raw/강수량(티센다각).csv` and `data/raw/기온_스플라인보간.csv`

## About `dataset_stage2.csv`
Script: [`../Preprocess/build_dataset_stage2.py`](../Preprocess/build_dataset_stage2.py)

Takes `dataset_stage1.csv` and cleans it up for modeling:

- Fixes bad sensor readings (zeros, physically impossible values, spikes, sudden dips) by turning them into missing values
- Fills a 35-day gap in turbidity data using matching dates from the 2022 dataset
- Fills in remaining missing values (interpolation)

---

## Sheet details

### RO1 (Reverse Osmosis)

: A process that uses high pressure to remove dissolved substances through a membrane.

| Column | Description | Unit |
|--------|-------------|------|
| `Date` | Timestamp | datetime |
| `운영차압` | Pressure difference across the membrane | bar |
| `비플럭스` | Specific flux (flow rate per membrane area) | LMH/bar |
| `원수 수온` | Feed water temperature | °C |
| `원수 탁도` | Feed water turbidity | NTU |
| `원수 TDS` | Total dissolved solids | mg/L |
| `원수 전기전도도` | Feed water conductivity | μS/cm |
| `원수 pH` | Feed water pH | - |
| `유입압력` | Inlet pressure | bar |
| `생산량` | Water produced per hour | m³/h |

`dataset_stage1.csv` and `dataset_stage2.csv` also include `is_operating` (whether the plant is running or in a cleaning/long-gap period), `cycle_id` (operating cycle number, 0 during cleaning), `rain`, and `temp`.

For basic statistics, missing-data rates, and outlier analysis, see [`../EDA/README.md`](../EDA/README.md).
