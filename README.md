# 거시지표 데이터 수집 도구

암호화폐 거래 불확실성 감소 모델의 입력 피처 생성을 위한 데이터 수집·전처리 파이프라인.
코스피(KOSPI)와 한국 채권 수익률 등 거시지표 5년치(2021-01-01 ~ 2025-12-31) 일단위 데이터를 수집한다.

---

## 프로젝트 구조

```
macro-collector/
├── src/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── kospi_collector.py
│   │   └── supplement_collector.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── manual_loader.py
│   ├── preprocessor.py
│   ├── feature_engineer.py
│   └── storage.py
├── inputs/
│   ├── bond/           # 채권 수익률 CSV (한국은행 홈페이지 수동 다운로드)
│   ├── sentiment/      # 김근환: 유튜브·뉴스 감정점수 CSV
│   ├── global_macro/   # 노정균(환율·금값) / 이찬희(나스닥·미국금리) CSV
│   └── crypto/         # 이준하: BTC·ETH CSV
├── outputs/
│   ├── raw/            # 소스별 원본 데이터 (Parquet + CSV)
│   └── processed/      # 전처리 완료 통합 DataFrame (Parquet + CSV)
├── config.py
├── collect.py
├── load_manual.py
├── process.py
├── main.py
└── requirements.txt
```

---

## 파일별 역할

### 진입점 (루트)

| 파일 | 역할 |
|------|------|
| `collect.py` | API 수집 전용 진입점. KOSPI OHLCV·수급을 수집해 `outputs/raw/`에 저장 |
| `load_manual.py` | 수동 CSV 로드 전용 진입점. `inputs/` 하위 CSV를 읽어 `outputs/raw/`에 저장 |
| `process.py` | 전처리·파생변수 전용 진입점. `outputs/raw/` 전체를 읽어 `outputs/processed/`에 저장. `collect.py` + `load_manual.py` 선행 실행 필수 |
| `main.py` | 풀 파이프라인 래퍼. `collect → load_manual → process` 순차 실행 |
| `config.py` | 전체 상수·하이퍼파라미터·경로 중앙 관리. 모든 모듈이 이 파일에서만 값을 가져온다 |

### `src/collectors/`

| 파일 | 역할 |
|------|------|
| `kospi_collector.py` | KOSPI 지수 OHLCV(시가·고가·저가·종가·거래량)와 외국인·기관·개인 순매수 수집. pykrx 기본, FinanceDataReader 보조 |
| `supplement_collector.py` | yfinance를 통한 KOSPI OHLCV 보완 수집. 기본 소스 결측 시 대체 데이터로 활용 |

### `src/loaders/`

| 파일 | 역할 |
|------|------|
| `manual_loader.py` | `inputs/` 하위 CSV를 읽어 날짜 인덱스 정규화(DatetimeIndex 변환, 시각 성분 제거) 후 `outputs/raw/`에 Parquet 저장. bond / sentiment / global_macro / crypto 카테고리별 처리 |

### `src/`

| 파일 | 역할 |
|------|------|
| `preprocessor.py` | 결측치·이상치 처리 및 한국 휴장일 마킹. 3σ 이상치 제거, 휴장일 NaN 마킹(forward fill 금지) |
| `feature_engineer.py` | 모델 입력용 파생 변수 생성. 로그 수익률, 20 거래일 rolling 변동성, 금리 스프레드(10Y-1Y, 3Y-1Y, 신용 스프레드) 계산 |
| `storage.py` | CSV + Parquet 이중 저장. `save_raw()` / `save_processed()` |

---

## 데이터 입력 및 출력 컬럼

### API 자동 수집 (`collect.py`)

| 카테고리 | 컬럼 | 소스 |
|---------|------|------|
| KOSPI OHLCV | `open, high, low, close, volume` | pykrx / FinanceDataReader / yfinance |
| KOSPI 수급 | `foreign_net, institution_net, retail_net` | pykrx (크레덴셜 없을 시 빈 DataFrame 허용) |

### 수동 CSV 입력 (`inputs/`)

| 담당 | 저장 경로 | 컬럼 |
|------|----------|------|
| 수동 다운로드 | `inputs/bond/` | `date, gov_1y, gov_3y, gov_5y, gov_10y, gov_20y, gov_30y, msc_91d, msc_1y, msc_2y, corp_aa, corp_bbb, base_rate` |
| 김근환 | `inputs/sentiment/` | `date, sentiment_youtube, sentiment_news` |
| 노정균 | `inputs/global_macro/` | `date, usd_krw, gold_usd` |
| 이찬희 | `inputs/global_macro/` | `date, nasdaq_close, us_rate` |
| 이준하 | `inputs/crypto/` | `date, btc_close, eth_close` |

> CSV 공통 규칙: 첫 번째 컬럼 `date` (형식: `YYYY-MM-DD`), 컬럼명 영문 소문자

### 전처리 규칙

| 데이터 | 휴장일 마킹 | 이상치 제거(3σ) |
|--------|:---------:|:-------------:|
| KOSPI OHLCV / 채권 | ✅ | ✅ |
| global_macro / crypto / sentiment | ❌ | ✅ |

> 결측치(휴장일·이상치)는 NaN 유지 — forward fill 금지, 모델 레이어에서 처리

### 파생 변수 (`feature_engineer.py`)

| 컬럼 | 계산식 |
|------|--------|
| `log_return` | `log(close_t / close_{t-1})` |
| `volatility_20d` | 로그 수익률 20 거래일 rolling 표준편차 |
| `term_spread_10y1y` | `gov_10y - gov_1y` |
| `term_spread_3y1y` | `gov_3y - gov_1y` |
| `credit_spread_aa` | `corp_aa - gov_3y` |
| `credit_spread_bbb` | `corp_bbb - gov_3y` |

### 최종 산출물

| 파일 | 경로 | 규격 |
|------|------|------|
| `macro_features.parquet` | `outputs/processed/` | 1,826행 × 29컬럼 (2021-01-01 ~ 2025-12-31) |
| `macro_features.csv` | `outputs/processed/` | 동일 내용 CSV |

---

## 실행 방법

```bash
# 환경 설정
pip install -r requirements.txt

# Windows 한국어 로그 깨짐 방지 (필수)
set PYTHONIOENCODING=utf-8

# 1단계: API 수집 (KOSPI)
python collect.py

# 2단계: 수동 CSV 로드 (inputs/ → outputs/raw/)
python load_manual.py

# 3단계: 전처리 및 파생변수 생성
python process.py

# 전체 파이프라인 한 번에 실행
python main.py
```

---

## 의존성

```
pykrx
FinanceDataReader
yfinance
pandas
pyarrow
requests
```

전체 목록: `requirements.txt` 참고
