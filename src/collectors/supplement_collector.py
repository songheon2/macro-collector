import logging

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(config.RETRY_ATTEMPTS), wait=wait_fixed(config.RETRY_WAIT_SECONDS))
def fetch_kospi_yfinance(start: str, end: str) -> pd.DataFrame:
    """yfinance로 KOSPI OHLCV 수집 (기본 소스 결측 시 대체용)."""
    logger.info("yfinance KOSPI 수집 시작: %s ~ %s", start, end)

    ticker = yf.Ticker(config.KOSPI_YFINANCE_TICKER)
    df = ticker.history(start=start, end=end, auto_adjust=True)

    if df.empty:
        raise RuntimeError(f"yfinance에서 데이터를 가져오지 못했습니다: {config.KOSPI_YFINANCE_TICKER}")

    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"

    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=rename_map)
    cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[cols]

    logger.info("yfinance KOSPI 수집 완료: %d 행", len(df))
    return df


def merge_with_fallback(df_primary: pd.DataFrame, df_fallback: pd.DataFrame) -> pd.DataFrame:
    """기본 소스의 결측일을 보완 소스로 채운다."""
    missing_dates = df_primary.index[df_primary.isnull().all(axis=1)]
    if missing_dates.empty:
        return df_primary

    logger.info("보완 소스로 대체할 날짜 수: %d", len(missing_dates))
    df_fill = df_fallback.reindex(missing_dates)
    df_primary.update(df_fill)
    return df_primary
