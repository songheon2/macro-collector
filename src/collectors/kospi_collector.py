import logging
from typing import Optional

import pandas as pd
import FinanceDataReader as fdr
from tenacity import retry, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(config.RETRY_ATTEMPTS), wait=wait_fixed(config.RETRY_WAIT_SECONDS))
def fetch_kospi_ohlcv(start: str, end: str) -> pd.DataFrame:
    """FinanceDataReader로 KOSPI OHLCV + 거래량 수집, pykrx로 거래대금 보완."""
    logger.info("KOSPI OHLCV 수집 시작: %s ~ %s", start, end)

    df_fdr = fdr.DataReader("KS11", start=start, end=end)
    df_fdr.index = pd.to_datetime(df_fdr.index)
    df_fdr.index.name = "date"

    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df_fdr = df_fdr.rename(columns=rename_map)
    cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df_fdr.columns]
    df_fdr = df_fdr[cols]

    # pykrx로 거래대금 추가
    try:
        df_fdr = _merge_krx_ohlcv(df_fdr, start, end)
    except Exception as exc:
        logger.warning("pykrx OHLCV 병합 실패 (거래대금 제외): %s", exc)

    logger.info("KOSPI OHLCV 수집 완료: %d 행", len(df_fdr))
    return df_fdr


def _merge_krx_ohlcv(df_base: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """pykrx에서 거래대금(trading_value) 가져와 병합."""
    from pykrx import stock

    fromdate = start.replace("-", "")
    todate = end.replace("-", "")
    df_krx = stock.get_index_ohlcv_by_date(fromdate, todate, config.KOSPI_INDEX_TICKER)
    df_krx.index = pd.to_datetime(df_krx.index)
    df_krx.index.name = "date"

    # 거래대금 컬럼 추출 (pykrx 버전마다 컬럼명 상이)
    trading_col: Optional[str] = None
    for candidate in ["거래대금", "TradingValue", "trading_value"]:
        if candidate in df_krx.columns:
            trading_col = candidate
            break

    if trading_col:
        df_base = df_base.join(df_krx[[trading_col]].rename(columns={trading_col: "trading_value"}), how="left")
    else:
        logger.warning("pykrx 거래대금 컬럼을 찾지 못했습니다. 컬럼 목록: %s", df_krx.columns.tolist())

    return df_base


@retry(stop=stop_after_attempt(config.RETRY_ATTEMPTS), wait=wait_fixed(config.RETRY_WAIT_SECONDS))
def fetch_kospi_supply(start: str, end: str) -> pd.DataFrame:
    """pykrx로 KOSPI 외국인·기관·개인 순매수 수집."""
    logger.info("KOSPI 수급 데이터 수집 시작: %s ~ %s", start, end)

    from pykrx import stock

    fromdate = start.replace("-", "")
    todate = end.replace("-", "")

    df = stock.get_market_trading_value_by_date(fromdate, todate, "KOSPI")
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"

    # 컬럼 정규화 (pykrx 버전 대응)
    col_map = _detect_supply_columns(df.columns.tolist())
    df = df.rename(columns=col_map)

    keep = [c for c in ["foreign_net", "institution_net", "retail_net"] if c in df.columns]
    if not keep:
        raise RuntimeError(f"수급 컬럼을 인식할 수 없습니다. 원본 컬럼: {df.columns.tolist()}")

    df = df[keep]
    logger.info("KOSPI 수급 수집 완료: %d 행, 컬럼: %s", len(df), keep)
    return df


def _detect_supply_columns(cols: list) -> dict:
    """pykrx 버전별 컬럼명 차이를 정규화하는 맵 반환."""
    mapping: dict = {}
    for col in cols:
        if "외국인" in col:
            mapping[col] = "foreign_net"
        elif "기관" in col:
            mapping[col] = "institution_net"
        elif "개인" in col:
            mapping[col] = "retail_net"
    return mapping
