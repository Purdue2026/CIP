# EDA (탐색적 데이터 분석)

`data/`의 원본·가공 데이터에 대한 통계 요약, 품질 이슈, 상관관계·결측치·운전 사이클 분석 결과를 정리합니다. 데이터 자체(파일 구성, 컬럼 설명)는 [`../data/README.md`](../data/README.md) 참고.

> 이 파일은 **이상치 탐지·결측치 보간이 아직 적용되지 않은 1차본**으로, 운전 사이클 정의(`cycle_id`/`is_operating`)와 기상데이터(`rain`/`temp`) 병합만 되어 있습니다. 이상치·결측치 처리는 다음 단계(`dataset_stage2.csv`, 미착수)에서 별도로 진행할 예정입니다.

```
EDA/
├── README.md
├── scripts/    # 분석 스크립트 (project 루트에서 실행)
├── results/    # 분석 결과 텍스트
└── plots/      # 그림(png) — plots/cycles/ 사이클별 상세, plots/notion_svg/ Notion 임베딩용 수동 파일
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

## 데이터 품질 이슈

### 결측값
- **RO1**: `운영차압`, `비플럭스`, `유입압력`, `생산량`에서 약 25~27%의 결측 발생 → 설비 정지 또는 센서 오류 구간으로 추정 (자세한 수치는 `results/stage1_pipeline_results.txt` 참고)

### 이상값
- 원수 수온, TDS, 전기전도도, pH 등에서 `0` 값 → 센서 미측정 또는 결측 처리 필요
- `원수 탁도` 최댓값이 일반 범위(< 2 NTU)를 크게 초과하는 구간 존재

### 상관관계
- TDS ↔ 전기전도도 **r = 1.000** (완전 선형) → 다중공선성 방지를 위해 하나만 입력 변수로 사용 권장
- `dataset_stage1.csv` 기준 |r|≥0.5 강한 상관: 원수 수온↔유입압력(-0.894), 원수 TDS↔유입압력(0.834), temp↔원수 수온(0.831), 운영차압↔유입압력(0.764), 원수 수온↔원수 TDS(-0.731), temp↔유입압력(-0.724), temp↔원수 TDS(-0.630)
- 비플럭스(핵심 지표)는 개별 변수 어느 것과도 강한 선형관계가 없음 (가장 큰 상관도 temp(-0.355), 운영차압(-0.313), 원수 수온(-0.285) 수준으로 전부 |r|<0.5) → 단일 변수로는 막 오염을 설명할 수 없고, 여러 변수의 누적 효과를 학습하는 비선형 시계열 모델(LSTM 등)이 필요하다는 근거
- 상세 상관계수 행렬, 시차(lag) 교차상관, 산점도는 [`results/eda_correlation_results.txt`](results/eda_correlation_results.txt)와 `plots/corr_heatmap_*.png`, `plots/lag_correlation_비플럭스.png`, `plots/scatter_*.png` 참고

### 운전 사이클
- 비플럭스·운영차압의 결측 시점이 서로 강하게 겹침 → 센서 오류가 아니라 설비 전체 정지(세척/점검)로 판단
- 비플럭스 결측 20시간 이상 지속 구간(4시간 이하 짧은 값은 흡수) 중, 구간 전후 10개 값 중앙값 비교로 비플럭스 5%↑ **OR** 운영차압 5%↓ 중 하나라도 만족하면 "세척"으로 인정 → **운전 사이클 10개** 도출 (연말 트레일링 조각 제외)
- 상세 로직은 [`scripts/build_dataset_stage1.py`](scripts/build_dataset_stage1.py)의 `detect_cleaning_cycles()` 참고, 사이클별 시계열은 `plots/cycles_overview.png`·`plots/cycles/cycle_01~10_vars.png`, 사이클별 길이는 `plots/cycle_duration.png` 참고

---

## 분석 결과 파일 안내

| 분석 | 스크립트 | 결과 | 관련 그림 |
|---|---|---|---|
| **1차 데이터셋 생성 (현재, 이상치/결측치 처리 전)** — 운전 사이클 정의 + 기상데이터 병합 | `scripts/build_dataset_stage1.py` | `results/stage1_pipeline_results.txt` → `data/processed/dataset_stage1.csv` | `plots/cycles_overview.png` |
| 시계열/분포 시각화 (raw dataset1, 2021년) | `scripts/visualize_ro1.py` | - | `plots/timeseries_*.png`, `plots/hist_*.png`, `plots/overview_dataset1.png` |
| 사이클별 시계열 상세 (dataset_stage1.csv 기준, 10개) | `scripts/visualize_cycles.py` | - | `plots/cycles_overview.png`, `plots/cycles/cycle_01~10_vars.png` |
| 사이클별 지속시간 막대그래프 | `scripts/visualize_cycle_duration.py` | - | `plots/cycle_duration.png` |
| 상관관계·시차·산점도 분석 (dataset1 raw + dataset_stage1.csv) | `scripts/correlation_analysis.py` | `results/eda_correlation_results.txt` | `plots/corr_heatmap_dataset1.png`, `plots/corr_heatmap_stage1.png`, `plots/lag_correlation_비플럭스.png`, `plots/scatter_*.png` |

모든 스크립트는 project 루트에서 실행합니다 (예: `./venv/bin/python3 EDA/scripts/build_dataset_stage1.py`).