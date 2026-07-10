# 데이터 설명

수처리 시설(RO 멤브레인 공정)의 시간별 운영 데이터셋. 
상위 프로젝트 개요는 [`../README.md`](../README.md) 참고.

---

## 파일 구성

| 파일명 | 위치 | 기간 | 행수 | 비고 |
|--------|------|------|------|------|
| `kwater_recipe06_dataset1.xlsx` | `raw/` | 2021-01-01 ~ 2021-12-31 | 8,760행 (RO1 시트) | 원본, **사용** |
| `kwater_recipe06_dataset2.xlsx` | `raw/` | 2022-01-01 ~ 2022-06-30 | 4,344행 (RO1 시트) | 원본, ⚠️ **미사용** (2022년 데이터는 분석에서 제외) |
| `강수량(티센다각).csv` | `raw/` | 2021-01-01 ~ 2022-07-05 | 13,200행 | 원본 기상(강수량), **사용** — `dataset_stage1.csv`의 rain 출처 |
| `기온_스플라인보간.csv` | `raw/` | 2021-01-01 ~ 2022-12-31 | 17,467행 | 원본 기상(기온), **사용** — `dataset_stage1.csv`의 temp 출처 |
| `dataset_stage1.csv` | `processed/` | 2021-01-01 ~ 2021-12-31 | 8,760행 | **현재 1차본** — 이상치/결측치 처리 전, 운전 사이클 정의 + 기상데이터만 병합 |

- 측정 간격: **1시간** (시각 형식: `YYYY-MM-DD HH:00:01`)
- **2021년(dataset1) 데이터만 사용합니다.** dataset2(2022년 상반기)는 분석 범위에서 제외

---

## `dataset_stage1.csv` 설명

생성 스크립트: [`../EDA/scripts/build_dataset_stage1.py`](../EDA/scripts/build_dataset_stage1.py), 
결과 로그: [`../EDA/logs/stage1_pipeline_results.txt`](../EDA/logs/stage1_pipeline_results.txt)

- 이상치·결측치 처리 없음
- 운전 사이클 정의(`cycle_id`, `is_operating`)
- 기상데이터: `data/raw/강수량(티센다각).csv`, `data/raw/기온_스플라인보간.csv` 병합
---

## 시트 설명

### RO1 (역삼투 공정, Reverse Osmosis)

: 고압으로 반투막을 통해 용존 물질을 제거하는 공정

| 컬럼 | 설명 | 단위 |
|------|------|------|
| `Date` | 측정 일시 | datetime |
| `운영차압` | 막 전후 압력 차 | bar |
| `비플럭스` | 단위 면적당 투과 유량 (Specific Flux) | LMH/bar |
| `원수 수온` | 유입 원수 온도 | °C |
| `원수 탁도` | 유입 원수 탁도 | NTU |
| `원수 TDS` | 총 용존 고형물 | mg/L |
| `원수 전기전도도` | 유입 원수 전기전도도 | μS/cm |
| `원수 pH` | 유입 원수 수소이온농도 | - |
| `유입압력` | 막 유입 측 압력 | bar |
| `생산량` | 시간당 생산 수량 | m³/h |

`dataset_stage1.csv`는 위 컬럼 외에 `is_operating`(세척/장기결측 구간 여부), `cycle_id`(운전 사이클 번호, 세척 구간은 0), `rain`(강수량), `temp`(기온)를 포함.

기초 통계, 결측률, 이상값 등 데이터 품질 분석 결과는 [`../EDA/README.md`](../EDA/README.md)를 참고.