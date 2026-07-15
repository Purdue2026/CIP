# RO Dataset

An ML and optimization project that uses hourly operating data from a water treatment plant (RO membrane process) to study membrane fouling and find the right time to clean (CIP).

---

## Folder Structure

```
purdue_project/
├── README.md
├── data/               # raw and processed data
│   ├── raw/            # raw xlsx files
│   └── processed/      # dataset_stage1.csv (step 1) → dataset_outliers_removed.csv (step 2a) → dataset_stage2.csv (step 2b, cleaned up)
├── EDA/                # exploratory data analysis
│   ├── scripts/        # analysis scripts
│   ├── logs/           # result logs (txt)
│   └── plots/          # charts (png)
├── Preprocess/         # preprocessing scripts - remove_outliers.py, fill_missing.py turn dataset_stage1.csv into dataset_stage2.csv
│   └── plots/          # before/after charts (png)
├── ML/                 # flux prediction models (Ridge vs LSTM), results in ML/plots, ML/results
├── Optimization/       # cleaning (CIP) threshold optimization
├── docs/               # reference documents (reports, papers, etc.)
└── venv/
```

## How to Run

Run all analysis scripts from the project root directory.

```bash
./venv/bin/python3 EDA/scripts/build_dataset_stage1.py
```
