# ── 수집 기간 ──────────────────────────────────────────────────────────────
START_DATE: str = "2021-01-01"
END_DATE: str = "2025-12-31"

# ── 경로 ──────────────────────────────────────────────────────────────────
RAW_DIR: str = "outputs/raw"
PROC_DIR: str = "outputs/processed"

# ── 전처리 파라미터 ────────────────────────────────────────────────────────
OUTLIER_SIGMA: float = 3.0
ROLLING_WINDOW: int = 20

# ── API 재시도 설정 ────────────────────────────────────────────────────────
RETRY_ATTEMPTS: int = 3
RETRY_WAIT_SECONDS: int = 5

# ── KRX / pykrx 설정 ──────────────────────────────────────────────────────
KOSPI_INDEX_TICKER: str = "1001"   # pykrx KOSPI 지수 티커
KOSPI_YFINANCE_TICKER: str = "^KS11"
