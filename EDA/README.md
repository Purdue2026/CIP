# EDA (탐색적 데이터 분석)

`data/`의 원본·가공 데이터에 대한 통계 요약, 품질 이슈, 상관관계·결측치·운전 사이클 분석 결과를 정리합니다. 데이터 자체(파일 구성, 컬럼 설명)는 [`../data/README.md`](../data/README.md) 참고.

> 이 파일은 **이상치 탐지·결측치 보간이 아직 적용되지 않은 1차본**으로, 운전 사이클 정의(`cycle_id`/`is_operating`)와 기상데이터(`rain`/`temp`) 병합만 되어 있습니다. 이상치·결측치 처리는 다음 단계(`dataset_stage2.csv`)에서 별도로 진행합니다.

```
EDA/
├── README.md
├── scripts/    # 분석 스크립트 (project 루트에서 실행)
├── logs/       # 분석 결과 텍스트
└── plots/      # 그림(png)
```

---

## 기초 통계 요약 (Dataset1, 2021년 전체, 8,760행)

| 컬럼 | 평균 | 최솟값 | 최댓값 | 표준편차 | 결측률 |
|------|------|--------|--------|---------|--------|
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

## 분석 결과 파일

| 분석 | 스크립트 | 결과 | 관련 그림 |
|---|---|---|---|
| **1차 데이터셋 생성 (현재, 이상치/결측치 처리 전)** — 운전 사이클 정의 + 기상데이터 병합 | `scripts/build_dataset_stage1.py` | `logs/stage1_pipeline_results.txt` → `data/processed/dataset_stage1.csv` | `plots/cycles_overview.png` |
| 시계열/분포 시각화 (raw dataset1, 2021년) | `scripts/visualize_ro1.py` | - | `plots/timeseries_*.png`, `plots/hist_*.png`, `plots/overview_dataset1.png` |
| 사이클별 시계열 개요 (dataset_stage1.csv 기준, 10개) | `scripts/visualize_cycles.py` | - | `plots/cycles_overview.png` |
| 사이클별 지속시간 막대그래프 | `scripts/visualize_cycle_duration.py` | - | `plots/cycle_duration.png` |
| 상관관계·시차·산점도 분석 (dataset_stage1.csv 기준) | `scripts/correlation_analysis.py` | `logs/eda_correlation_results.txt` | `plots/corr_heatmap_stage1.png`, `plots/lag_correlation_비플럭스.png`, `plots/scatter_*.png` |

모든 스크립트는 project 루트에서 실행합니다 (예: `./venv/bin/python3 EDA/scripts/build_dataset_stage1.py`).