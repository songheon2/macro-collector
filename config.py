import os

# ── 수집 기간 ──────────────────────────────────────────────────────────────
START_DATE: str = "2021-01-01"
END_DATE: str = "2025-12-31"

# ── 경로 ──────────────────────────────────────────────────────────────────
RAW_DIR: str = "outputs/raw"
PROC_DIR: str = "outputs/processed"

# ── 전처리 파라미터 ────────────────────────────────────────────────────────
OUTLIER_SIGMA: float = 3.0
ROLLING_WINDOW: int = 20

# ── 한국은행 ECOS API ──────────────────────────────────────────────────────
# ECOS_API_KEY: 환경변수 ECOS_API_KEY 우선, 없으면 아래 값 사용
ECOS_API_KEY: str = os.environ.get("ECOS_API_KEY", "3I2K2N33FHZ31S98I2KO")
ECOS_BASE_URL: str = "https://ecos.bok.or.kr/api"

# ECOS 통계표 코드 — 실제 사용 전 https://ecos.bok.or.kr/api/ 에서 검증 필수
ECOS_STAT_CODE_BOND: str = "817Y002"       # 채권수익률(주요)
ECOS_STAT_CODE_BASE_RATE: str = "722Y001"  # 한국은행 기준금리

# 채권 item code 맵 — 창 1 검증 후 수정
ECOS_BOND_ITEMS: dict[str, str] = {
    "gov_1y":   "010190000",  # 국고채 1년
    "gov_3y":   "010200000",  # 국고채 3년
    "gov_5y":   "010200001",  # 국고채 5년
    "gov_10y":  "010210000",  # 국고채 10년
    "gov_20y":  "010220000",  # 국고채 20년
    "gov_30y":  "010230000",  # 국고채 30년
    "msc_91d":  "010400000",  # 통화안정증권 91일
    "msc_1y":   "010400001",  # 통화안정증권 1년
    "msc_2y":   "010400002",  # 통화안정증권 2년
    "corp_aa":  "010300000",  # 회사채 3년 AA-
    "corp_bbb": "010320000",  # 회사채 3년 BBB-
}
ECOS_BASE_RATE_ITEM: str = "0101000"  # 기준금리 item code

# ── API 재시도 설정 ────────────────────────────────────────────────────────
RETRY_ATTEMPTS: int = 3
RETRY_WAIT_SECONDS: int = 5

# ── KRX / pykrx 설정 ──────────────────────────────────────────────────────
KOSPI_INDEX_TICKER: str = "1001"   # pykrx KOSPI 지수 티커
KOSPI_YFINANCE_TICKER: str = "^KS11"
