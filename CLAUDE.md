# 암호화폐 불확실성 감소 모델 — 거시지표 데이터 수집 도구

> 목적: 코스피(KOSPI)와 한국 채권 수익률 5년치 일단위 데이터를 수집·전처리해,
> 암호화폐 거래에서 발생하는 불확실성을 줄이는 모델의 입력 피처를 생성한다.

---

## 세션 시작 명령어

| 창 | 역할 | 시작 명령 |
|----|------|-----------|
| 창 1 | 설계 담당 | `claude "[설계 담당] CLAUDE.md를 읽고 설계 담당으로 시작해."` |
| 창 2 | 코딩 담당 | `claude "[코딩 담당] CLAUDE.md와 CLAUDE.local.md를 읽고 코딩 담당으로 시작해."` |
| 창 3 | 리뷰 담당 | `claude "[리뷰 담당] CLAUDE.md를 읽고 현재 구현된 파일을 리뷰해."` |

---

## 역할 정의

### [설계 담당] — 창 1
- **목적**: 아키텍처 설계 유지, 모듈 간 인터페이스 정의, 구현 규칙 관리
- **행동 규칙**:
  - 코드를 직접 작성하지 않는다. 설계와 지시만 한다.
  - 설계 변경 시 이 CLAUDE.md를 즉시 업데이트한다.
  - 창 3(리뷰)의 제안은 반드시 창 1이 최종 판단한다.
    - 설계 의도에 부합 → CLAUDE.md 수정 후 창 2에 변경 지시
    - 설계 의도와 불일치 → 기각, 창 2에 원래 설계 유지 지시
  - CLAUDE.md는 항상 **single source of truth**로 유지한다.
- **세션 시작 확인 문구**:
  > "설계 담당으로 시작합니다. CLAUDE.md 기준으로 현재 설계 상태를 요약할게요."

---

### [코딩 담당] — 창 2
- **목적**: CLAUDE.md 설계 기반으로 실제 코드 구현
- **행동 규칙**:
  - 하이퍼파라미터·상수·API 키·경로 하드코딩 금지. 반드시 `config.py`에서만 가져온다.
  - 타입 힌트 필수, 로깅은 `logging` 모듈 사용 (`print` 금지).
  - 불명확한 사항은 CLAUDE.local.md에 질문으로 기록한다.
  - 파일 완성 시 CLAUDE.local.md 진행상황을 업데이트한다.
  - 창 3의 리뷰 제안은 창 1 확인 없이 절대 반영하지 않는다.
- **절대 금지 행동** (창 1 명시 지시 없이 독자적으로 해서는 안 되는 행동):
  - `config.py` 값(상수·코드·경로 포함) 임의 수정
  - 설계 명세에 없는 함수·모듈·파일 추가
  - 지시받은 파일 외 다른 파일 수정 (리뷰 수정 범위 초과 포함)
  - 설계 의도와 다르다고 판단되는 로직을 "더 나을 것 같아서" 변경
- **판단 불명확 시 행동 원칙**:
  - 구현 중 판단이 필요한 사항이 생기면 **멈추고** CLAUDE.local.md에 질문 기록 후 창 1 답변 대기
  - 추정으로 진행하지 않는다. 추정이 불가피한 경우 반드시 CLAUDE.local.md에 추정 내용과 근거를 명시
- **세션 시작 확인 문구**:
  > "코딩 담당으로 시작합니다. CLAUDE.local.md에서 진행상황 확인 후 이어서 구현할게요."

---

### [리뷰 담당] — 창 3
- **목적**: 구현된 코드가 설계 의도와 데이터 품질 기준에 맞는지 독립적으로 검토
- **행동 규칙**:
  - 코드를 직접 수정하지 않는다. 문제점과 개선 제안만 리포트한다.
  - CLAUDE.md 설계 기준과 실제 코드를 반드시 대조한다.
  - 리뷰 형식: `[PASS]` / `[WARN]` / `[FAIL]` (파일명·위치·이유 명시)
  - 데이터 수집 특성상 **API 에러 처리**, **결측치 전략**, **날짜 정합성** 을 중점 검토한다.
- **세션 시작 확인 문구**:
  > "리뷰 담당으로 시작합니다. 현재 구현된 파일을 확인하고 리뷰를 시작할게요."

---

## 역할 간 의사결정 흐름

```
창 3 (리뷰) → 개선 제안 → 창 1 (설계) → 판단
                                  ├── 승인: CLAUDE.md 수정 → 창 2에 변경 지시
                                  └── 기각: 창 2에 원래 설계 유지 지시
```

> 창 2(코딩)는 창 1의 지시 없이 리뷰 제안을 직접 반영하지 않는다.

---

## 프로젝트 구조

```
Tool/
├── src/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── kospi_collector.py       # KRX / FinanceDataReader / yfinance
│   │   └── supplement_collector.py  # 외국인·기관 수급, 보완 소스 통합
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── manual_loader.py         # inputs/ CSV 읽기·정규화 → outputs/raw/ 저장
│   ├── preprocessor.py              # 결측치·이상치 처리, 휴장일 마킹
│   ├── feature_engineer.py          # 파생 변수 계산 (수익률, 변동성, 스프레드)
│   ├── scaler.py                    # 2차 전처리: 로그 차분 + MinMax 정규화
│   └── storage.py                   # CSV / Parquet 저장
├── inputs/                          # 팀원 수동 제공 CSV 저장소 (git 제외)
│   ├── bond/                        # 채권 수익률 CSV (한국은행 홈페이지 수동 다운로드)
│   ├── sentiment/                   # 김근환: 유튜브 제목·뉴스 헤드라인 감정점수
│   ├── global_macro/                # 노정균: 환율·금값 / 이찬희: 나스닥·미국 금리
│   └── crypto/                      # 이준하: 비트코인·이더리움
├── outputs/
│   ├── raw/                         # 원본 데이터 (소스별 분리 저장)
│   └── processed/                   # 전처리 완료 통합 DataFrame
├── config.py                        # 전체 상수·파라미터 중앙 관리
├── collect.py                       # 수집 전용 진입점 (STEP 1~3)
├── load_manual.py                   # 수동 CSV 로드 진입점 (inputs/ → outputs/raw/)
├── process.py                       # 전처리·파생변수 전용 진입점 (STEP 4~6)
├── scale.py                         # 2차 전처리 진입점 (로그 차분 → MinMax, process.py 선행 필수)
├── main.py                          # 풀 파이프라인 래퍼 (collect → load_manual → process)
├── requirements.txt
├── CLAUDE.md                        # 이 파일 (single source of truth)
└── CLAUDE.local.md                  # 로컬 진행상황·질문 기록 (git 제외)
```

---

## 수집 대상 데이터 명세

### KOSPI (`kospi_collector.py`)
| 항목 | 소스 | 비고 |
|------|------|------|
| 시가 / 고가 / 저가 / 종가 | FinanceDataReader / yfinance | 보조 소스로 상호 검증 |
| 거래량 / 거래대금 | KRX Open API (pykrx) | |
| 외국인·기관·개인 순매수 | KRX Open API (pykrx) | **선택적 피처** — KRX 크레덴셜 없을 시 빈 DataFrame 허용 |
| 선물 미결제약정 | 미정 (미구현) | KRX 크레덴셜 확보 후 재논의 |

### 수동 CSV 데이터 (`inputs/`)
| 담당 | 항목 | 저장 경로 | 컬럼 규칙 |
|------|------|-----------|-----------|
| 수동 다운로드 | 국고채 1Y/3Y/5Y/10Y/20Y/30Y, 통안채 91D/1Y/2Y, 회사채 AA-/BBB-, 기준금리 | `inputs/bond/` | date, gov_1y, gov_3y, gov_5y, gov_10y, gov_20y, gov_30y, msc_91d, msc_1y, msc_2y, corp_aa, corp_bbb, base_rate |
| 김근환 | 유튜브 제목·뉴스 헤드라인 감정점수 | `inputs/sentiment/` | date, sentiment_youtube, sentiment_news |
| 노정균 | 환율(USD/KRW), 금값(USD/oz) | `inputs/global_macro/` | date, usd_krw, usdkrw_return, gold_usd, gold_return |
| 이찬희 | 나스닥 지수, 미국 금리 | `inputs/global_macro/` | date, nasdaq_close, nasdaq_high, nasdaq_low, nasdaq_open, nasdaq_volume, us_rate, us_rate_high, us_rate_low, us_rate_open, us_rate_volume |
| 이준하 | 비트코인·이더리움 OHLCV + 기술적 지표 | `inputs/crypto/` | date, btc_open, btc_high, btc_low, btc_close, btc_volume, btc_value, btc_sma, btc_ema, btc_bb_lower, btc_bb_middle, btc_bb_upper, btc_rsi, eth_open, eth_high, eth_low, eth_close, eth_volume, eth_value, eth_sma, eth_ema, eth_bb_lower, eth_bb_middle, eth_bb_upper, eth_rsi |

> **CSV 공통 규칙**:
> - 첫 번째 컬럼은 반드시 `date` (형식: `YYYY-MM-DD`)
> - 컬럼명은 위 표의 영문 소문자 기준으로 통일
> - 기간: 2021-01-01 ~ 2025-12-31

### 수집 기간 및 주기
| 항목 | 내용 |
|------|------|
| 기간 | 2021-01-01 ~ 2025-12-31 (5년) |
| 단위 | 영업일 기준 일단위 |
| 예상 레코드 | 약 1,250일 |

---

## 모듈별 역할 및 인터페이스

### `config.py`
- **역할**: 모든 상수·하이퍼파라미터·API 키·경로 중앙 관리
- **포함 항목**:
  ```python
  START_DATE: str = "2021-01-01"
  END_DATE:   str = "2025-12-31"
  RAW_DIR:  str = "outputs/raw"
  PROC_DIR: str = "outputs/processed"
  OUTLIER_SIGMA: float = 3.0      # 이상치 제거 기준
  ROLLING_WINDOW: int = 20        # 변동성 계산 rolling window
  RETRY_ATTEMPTS: int = 3         # API 재시도 횟수 (KOSPI 컬렉터 공용)
  RETRY_WAIT_SECONDS: int = 5     # API 재시도 대기 시간
  ```

### `src/collectors/kospi_collector.py`
- **역할**: KOSPI 지수 및 수급 데이터 수집
- **핵심 함수**:
  - `fetch_kospi_ohlcv(start: str, end: str) -> pd.DataFrame`
  - `fetch_kospi_supply(start: str, end: str) -> pd.DataFrame`

### `src/collectors/supplement_collector.py`
- **역할**: yfinance 등 보완 소스 통합, 기본 소스 결측 시 대체
- **핵심 함수**:
  - `fetch_kospi_yfinance(start: str, end: str) -> pd.DataFrame`
- **수집 정책**: collect.py는 yfinance를 **항상(무조건) 수집**한다. 결측 발생 여부를 사전에 알 수 없고, 수집 시점에 추가 네트워크 오류가 발생할 수 있으므로 미리 확보하는 것이 안전하다.

### `src/preprocessor.py`
- **역할**: 결측치·이상치 처리, 한국 휴장일 마킹
- **핵심 함수**:
  - `mark_holidays(df: pd.DataFrame) -> pd.DataFrame` — 휴장일 NaN 마킹
  - `remove_outliers(df: pd.DataFrame, sigma: float) -> pd.DataFrame` — 3σ 기준 제거
  - `fill_missing(df: pd.DataFrame) -> pd.DataFrame` — 1단계: 이상치 NaN 선형 보간(limit=1), 2단계: 휴장일 NaN ffill

### `src/feature_engineer.py`
- **역할**: 모델 입력용 파생 변수 생성
- **핵심 함수**:
  - `calc_log_return(df: pd.DataFrame) -> pd.DataFrame` — `log(P_t / P_{t-1})`
  - `calc_rolling_volatility(df: pd.DataFrame, window: int) -> pd.DataFrame` — 20일 rolling std
  - `calc_yield_spreads(df: pd.DataFrame) -> pd.DataFrame` — 10Y-1Y, 3Y-1Y, 회사채(AA-/BBB-) - 국고채 3Y (신용 스프레드 기준 만기: gov_3y)

### `src/scaler.py`
- **역할**: 2차 전처리 — 가격·거래량 레벨 컬럼 로그 차분 후 전체 MinMax 정규화
- **핵심 함수**:
  - `log_diff_prices(df: pd.DataFrame) -> pd.DataFrame` — `_LOG_DIFF_COLS` 대상 `log(x_t / x_{t-1})` 적용. `close` 차분 후 `log_return` 중복 제거. 첫 행(NaN) 제거 후 반환
  - `minmax_scale(df: pd.DataFrame) -> pd.DataFrame` — `sklearn.MinMaxScaler` 전체 컬럼 [0, 1] 정규화
- **로그 차분 대상 컬럼** (`_LOG_DIFF_COLS`):
  - KOSPI: `open, high, low, close, volume`
  - Global macro 가격: `usd_krw, gold_usd, nasdaq_close/high/low/open/volume`
  - BTC: `btc_open/high/low/close/volume/value, btc_sma, btc_ema, btc_bb_lower/middle/upper`
  - ETH: `eth_open/high/low/close/volume/value, eth_sma, eth_ema, eth_bb_lower/middle/upper`
- **로그 차분 제외 컬럼** (이미 정상 시계열):
  - `volatility_20d`, 금리·채권 전체, 스프레드 전체, `usdkrw_return, gold_return`, `btc_rsi, eth_rsi`

### `src/storage.py`
- **역할**: 데이터 저장 (CSV + Parquet 이중 저장)
- **핵심 함수**:
  - `save_raw(df: pd.DataFrame, name: str) -> None`
  - `save_processed(df: pd.DataFrame, name: str) -> None`

### `src/loaders/manual_loader.py`
- **역할**: `inputs/` 하위 CSV를 읽어 날짜 인덱스 정규화 후 `outputs/raw/`에 Parquet 저장
- **핵심 함수**:
  - `load_bond(path: str) -> pd.DataFrame` → `outputs/raw/bond_raw.parquet`
  - `load_sentiment(path: str) -> pd.DataFrame` → `outputs/raw/sentiment_raw.parquet`
  - `load_global_macro(path: str) -> pd.DataFrame` → `outputs/raw/global_macro_raw.parquet`
  - `load_crypto(path: str) -> pd.DataFrame` → `outputs/raw/crypto_raw.parquet`
- **공통 처리**: date 컬럼 → DatetimeIndex 변환, 컬럼명 소문자 통일, 중복 날짜 제거

### `load_manual.py`
- **역할**: 수동 CSV 로드 전용 진입점. `inputs/` → `outputs/raw/` 변환 후 종료
- **선행 조건**: `inputs/` 하위 폴더에 CSV 파일 존재
- **실행 순서**:
  1. `inputs/bond/` CSV → `outputs/raw/bond_raw.parquet`
  2. `inputs/sentiment/` CSV → `outputs/raw/sentiment_raw.parquet`
  3. `inputs/global_macro/` CSV → `outputs/raw/global_macro_raw.parquet`
  4. `inputs/crypto/` CSV → `outputs/raw/crypto_raw.parquet`

### `collect.py`
- **역할**: API 수집 전용 진입점. KOSPI만 수집하고 raw 파일 저장 후 종료
- **실행 순서**:
  1. config 로드
  2. KOSPI OHLCV 수집 → `outputs/raw/kospi_ohlcv_raw.parquet`
  3. KOSPI 수급 수집 → `outputs/raw/kospi_supply_raw.parquet`

### `process.py`
- **역할**: 전처리·파생변수 전용 진입점. `outputs/raw/` 전체를 읽어서 실행
- **선행 조건**: `collect.py` + `load_manual.py` 실행 완료 (raw 파일 존재 여부 체크)
- **실행 순서**:
  1. raw 파일 전체 로드 (kospi, bond, sentiment, global_macro, crypto)
  2. 전처리 (결측·이상치)
  3. 파생 변수 생성
  4. 통합 저장 → `outputs/processed/macro_features.parquet`

### `scale.py`
- **역할**: 2차 전처리 전용 진입점. `macro_features.parquet`을 읽어 로그 차분 + MinMax 정규화 후 저장
- **선행 조건**: `process.py` 실행 완료 (`outputs/processed/macro_features.parquet` 존재 여부 체크)
- **실행 순서**:
  1. `macro_features.parquet` 로드
  2. `log_diff_prices()` — 가격·거래량 레벨 컬럼 로그 차분, 첫 행 제거
  3. `minmax_scale()` — 전체 컬럼 [0, 1] 정규화
  4. 저장 → `outputs/processed/macro_features_scaled.parquet`

### `main.py`
- **역할**: 풀 파이프라인 래퍼
- **실행 순서**: `collect` → `load_manual` → `process` 순차 실행

> 각 모듈의 상세 인터페이스는 구현 전에 창 1(설계)이 이 섹션을 먼저 채운다.

---

## 실행 방식

```bash
python collect.py        # API 수집 → outputs/raw/ 저장 (KOSPI)
python load_manual.py    # 수동 CSV 로드 → outputs/raw/ 저장 (채권, 감정, 글로벌, 크립토)
python process.py        # 전처리·파생변수 → outputs/processed/macro_features.parquet
python scale.py          # 2차 전처리 → outputs/processed/macro_features_scaled.parquet (process.py 선행 필수)
python main.py           # 전체 파이프라인 실행
```

- Jupyter Notebook 없음 — 순수 스크립트 기반
- 모든 출력은 `outputs/` 디렉토리에 저장
- `process.py`는 실행 시작 시 `outputs/raw/` 파일 존재 여부를 체크하고, 없으면 즉시 오류 발생
- Windows 실행 환경에서 한국어 로그 깨짐 방지를 위해 `PYTHONIOENCODING=utf-8` 설정 필수

```bash
# Windows 환경 실행 시 권장
set PYTHONIOENCODING=utf-8 && python collect.py
```

---

## 코딩 규칙

| 규칙 | 내용 |
|------|------|
| 상수·하이퍼파라미터 | `config.py`에서만 관리, 모듈 내 하드코딩 금지 |
| config.py 수정 | **창 1의 명시적 지시 후에만 수정 허용**. 지시 없는 임의 수정 금지 |
| API 키 | `config.py` 또는 환경변수, 코드 내 직접 삽입 금지 |
| 모듈 독립성 | 각 모듈은 독립적으로 `import` 가능하도록 설계 |
| 로깅 | `print` 대신 Python `logging` 모듈 사용 |
| 타입 힌트 | 모든 함수 시그니처에 타입 힌트 필수 |
| 날짜 처리 | 모든 날짜는 `str (YYYY-MM-DD)` 입력, 내부에서 `pd.Timestamp` 변환 |
| 결측치 전략 | 이상치 NaN → 선형 보간(limit=1), 휴장일 NaN → ffill. 두 단계 모두 concat 후 저장 직전 적용. 시계열 시작부 잔여 NaN은 모델 레이어에서 처리 |
| 에러 처리 | API 실패 시 재시도 로직 포함, 조용한 실패(silent fail) 금지. 단 수급 데이터(kospi_supply)는 선택적 피처로 ERROR 로그 출력 후 빈 DataFrame 허용 |
| 코드 스타일 | Jupyter Notebook 스타일 금지 (셀 단위 실행 가정 코드 작성 금지) |

---

## 구현 순서 (창 2 참고)

코딩 창은 아래 순서를 준수해 구현한다:

1. `requirements.txt`
2. `config.py`
3. `src/__init__.py`
4. `src/collectors/__init__.py`
5. `src/collectors/kospi_collector.py`
6. `src/collectors/supplement_collector.py`
8. `src/preprocessor.py`
9. `src/feature_engineer.py`
10. `src/storage.py`
11. `collect.py` ← 신규 (수집 전용 진입점)
12. `process.py` ← 신규 (전처리·파생변수 전용 진입점)
13. `main.py` ← 수정 (collect + process 래퍼로 변경)
14. `src/loaders/__init__.py` ← 신규
15. `src/loaders/manual_loader.py` ← 신규 (수동 CSV 로드·정규화)
16. `load_manual.py` ← 신규 (수동 CSV 로드 진입점)

> 순서를 변경할 경우 창 1(설계)이 이 목록을 업데이트하고 이유를 기록한다.

---

## 설계 변경 이력

| 날짜 | 변경 내용 | 이유 | 결정자 |
|------|-----------|------|--------|
| 2026-05-14 | 초기 설계 작성 | 프로젝트 시작 | 창 1 |
| 2026-05-15 | `main.py` 단일 진입점 → `collect.py` / `process.py` / `main.py` 3분리 | 수집만 먼저 실행하는 요구 반영 | 창 1 |
| 2026-05-15 | KOSPI 수급 피처를 선택적 항목으로 격하, 실패 시 빈 DataFrame 허용 | pykrx KRX API 전면 불가 (크레덴셜 미보유) | 창 1 |
| 2026-05-15 | process.py 빈 supply 방어 처리 승인 | 빈 DataFrame → mark_holidays ValueError 실행 검증 | 창 1 |
| 2026-05-15 | Windows 실행 시 PYTHONIOENCODING=utf-8 운영 정책 확정 | cp949 인코딩으로 한국어 로그 깨짐 | 창 1 |
| 2026-05-15 | yfinance 항상(무조건) 수집 정책 확정 | 결측 여부 사전 불명, 수집 시점 오류 위험 회피 | 창 1 |
| 2026-05-15 | credit spread 기준 만기 gov_3y로 명시 | feature_engineer 설계 문서 누락 보완 | 창 1 |
| 2026-05-15 | preprocessor 공휴일 취약점 수용 결정 | bdate_range + reindex 방식이 실제 KRX 캘린더를 데이터에서 도출하므로 취약점 아님 | 창 1 |
| 2026-05-15 | ECOS 통계코드·cycle="D" 검증 보류 | ECOS API 키 확보 선행 필요, 키 확보 즉시 검증 예정 | 창 1 |
| 2026-05-15 | 창 2 미지시 ECOS item code 수정 발견 — 잠정 유지 | API 키 없어 검증 불가, 확보 즉시 실 검증 필수. 코딩 규칙에 config.py 무지시 수정 금지 추가 | 창 1 |
| 2026-05-15 | 수동 CSV 통합 설계 추가 (inputs/ + load_manual.py + manual_loader.py) | 팀원 5명 분담 데이터(감정·글로벌·크립토) 수동 제공 방식 확정 | 창 1 |
| 2026-05-15 | 수집 기간 변경: 2021-05-14~2026-05-14 → 2021-01-01~2025-12-31 | 실제 데이터 기간 확정 | 창 1 |
| 2026-05-21 | 수동 데이터 전처리 정책 확정: `remove_outliers`만 적용, `mark_holidays` 미적용 | `mark_holidays`는 한국 시장 캘린더 기반. 크립토·글로벌 매크로는 주말 포함 거래 존재하므로 적용 제외. 최종 인덱스 1,826 달력일 유지 | 창 1 |
| 2026-05-21 | `volatility_20d` rolling 계산 기준 변경: 달력일 → 거래일 한정 | 달력일 기준 시 NaN 75.3% 발생. "20일"은 20 거래일이 설계 의도이며 거래일 한정 계산 시 결측률 ~35%로 정상화 | 창 1 |
| 2026-05-21 | ECOS API 제거, 채권 데이터 수동 CSV로 전환 | 채권 수익률 수동 CSV가 이미 동일 데이터 커버. bond_collector.py 삭제, inputs/bond/ 추가, load_manual에 load_bond 추가. base_rate는 bond CSV 마지막 컬럼으로 수동 포함 | 창 1 |
| 2026-05-21 | 결측치 처리 전략 변경: 모델 레이어 → 파이프라인 2단계 처리 | KOSPI/채권 ~35%, nasdaq ~31% 결측률이 모델 학습에 부담. 이상치 NaN은 선형 보간(limit=1), 휴장일 NaN은 ffill로 구분 처리. 이상치가 휴장일로 전파되는 것을 방지. concat 후 저장 직전 적용. 시작부 잔여 NaN은 모델 레이어에서 처리 | 창 1 |
| 2026-05-22 | crypto 컬럼 확장: 종가만 → OHLCV 전체 | inputs/crypto/ CSV에 OHLCV 데이터가 이미 존재하나 manual_loader가 close만 추출. BTC/ETH 각각 open·high·low·close·volume 전체 반영 | 창 1 |
| 2026-05-22 | crypto 기술적 지표 추가: value, SMA, EMA, BB_lower/middle/upper, RSI | inputs/crypto/ CSV 파일이 _features 접미사로 갱신되며 기술적 지표 컬럼 추가. manual_loader _COLUMN_MAP 키명·매핑 및 _EXPECTED_COLUMNS 업데이트 | 창 1 |
| 2026-05-22 | 2차 전처리 추가: 로그 차분 → MinMax 정규화 | 가격·거래량 레벨 컬럼 정상화(비정상 시계열 제거) 및 전체 피처 스케일 [0,1] 통일. src/scaler.py + scale.py 신규, 출력: macro_features_scaled.parquet | 창 1 |

> 설계 변경 시 반드시 이 테이블에 추가한다.

---

## CLAUDE.local.md 운영 규칙

- 창 2(코딩)가 단독으로 관리하는 로컬 파일
- git에 커밋하지 않는다 (`.gitignore`에 추가)
- 포함 내용:
  - 현재 구현 진행상황 (완료 / 진행 중 / 미착수)
  - 창 1에게 묻고 싶은 질문
  - 임시 메모 및 트러블슈팅 기록 (ECOS API 응답 이슈 등)
