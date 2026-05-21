import logging

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)

_PRICE_COLS = ["close", "open", "high", "low"]


def calc_log_return(df: pd.DataFrame) -> pd.DataFrame:
    """log(P_t / P_{t-1}) 계산. 대상: close 컬럼 (없으면 _PRICE_COLS 중 첫 번째)."""
    df = df.copy()
    target = next((c for c in _PRICE_COLS if c in df.columns), None)
    if target is None:
        raise ValueError(f"log return 계산 대상 컬럼 없음. 보유 컬럼: {df.columns.tolist()}")

    df["log_return"] = np.log(df[target] / df[target].shift(1))
    logger.info("log_return 계산 완료 (기준: %s)", target)
    return df


def calc_rolling_volatility(df: pd.DataFrame, window: int = config.ROLLING_WINDOW) -> pd.DataFrame:
    """log_return의 rolling std (연율화 없음, 모델에서 처리)."""
    df = df.copy()
    if "log_return" not in df.columns:
        raise ValueError("calc_log_return을 먼저 호출해야 합니다.")

    df[f"volatility_{window}d"] = df["log_return"].rolling(window=window, min_periods=window).std()
    logger.info("rolling_volatility_%dd 계산 완료", window)
    return df


def calc_yield_spreads(df: pd.DataFrame) -> pd.DataFrame:
    """채권 스프레드 파생변수 생성.

    - term_spread_10y1y: 국고채 10Y - 1Y (장단기 스프레드)
    - term_spread_3y1y:  국고채 3Y - 1Y
    - credit_spread_aa:  회사채 AA- - 국고채 3Y
    - credit_spread_bbb: 회사채 BBB- - 국고채 3Y
    """
    df = df.copy()
    _add_spread(df, "term_spread_10y1y", "gov_10y", "gov_1y")
    _add_spread(df, "term_spread_3y1y",  "gov_3y",  "gov_1y")
    _add_spread(df, "credit_spread_aa",  "corp_aa",  "gov_3y")
    _add_spread(df, "credit_spread_bbb", "corp_bbb", "gov_3y")
    logger.info("yield_spreads 계산 완료")
    return df


def _add_spread(df: pd.DataFrame, name: str, col_a: str, col_b: str) -> None:
    if col_a in df.columns and col_b in df.columns:
        df[name] = df[col_a] - df[col_b]
    else:
        missing = [c for c in [col_a, col_b] if c not in df.columns]
        logger.warning("스프레드 %s 계산 불가 — 컬럼 누락: %s", name, missing)
