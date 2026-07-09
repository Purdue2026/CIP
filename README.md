# K-Water Recipe06 Dataset

수처리 시설(RO 멤브레인 공정)의 시간별 운영 데이터를 기반으로, 막 오염(fouling) 진행과 세정(CIP) 시점을 분석하는 ML 및 최적화 프로젝트

---

## 폴더 구조

```
purdue_project/
├── README.md          # 이 파일 (프로젝트 개요, 폴더 안내)
├── data/               # 원본·가공 데이터 → data/README.md
│   ├── raw/            # 원본 xlsx (dataset1=2021년 사용, dataset2=2022년 미사용)
│   └── processed/      # dataset_stage1.csv (현재 1차본 — 이상치/결측치 처리 전, 사이클+기상만)
├── EDA/                # 탐색적 데이터 분석 → EDA/README.md
│   ├── scripts/        # 분석 스크립트 (모두 project 루트에서 실행)
│   ├── results/        # 분석 결과 txt
│   └── plots/          # 그림(png) — plots/cycles/ 사이클별 상세, plots/notion_svg/ Notion 임베딩용 수동 파일
├── docs/               # 참고자료 → docs/README.md
└── venv/
```

각 폴더의 상세 내용은 해당 폴더의 README 참고

- [`data/README.md`](data/README.md) — 데이터셋 파일 구성, 컬럼 설명, 로딩 예시
- [`EDA/README.md`](EDA/README.md) — 기초 통계, 데이터 품질 이슈, 상관관계·결측치·사이클 분석 결과

## 실행 방법

모든 분석 스크립트는 project 루트 디렉토리에서 실행

```bash
./venv/bin/python3 EDA/scripts/build_dataset_stage1.py
```
