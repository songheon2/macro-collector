import logging

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

_LOG_DIFF_COLS: list[str] = [
    "open", "high", "low", "close", "volume",
    "usd_krw", "gold_usd",
    "nasdaq_close", "nasdaq_high", "nasdaq_low", "nasdaq_open", "nasdaq_volume",
    "btc_open", "btc_high", "btc_low", "btc_close", "btc_volume", "btc_value",
    "btc_sma", "btc_ema", "btc_bb_lower", "btc_bb_middle", "btc_bb_upper",
    "eth_open", "eth_high", "eth_low", "eth_close", "eth_volume", "eth_value",
    "eth_sma", "eth_ema", "eth_bb_lower", "eth_bb_middle", "eth_bb_upper",
]


def log_diff_prices(df: pd.DataFrame) -> pd.DataFrame:
    """가격·거래량 컬럼에 로그 차분 적용.

    - _LOG_DIFF_COLS 중 df에 존재하는 컬럼만 처리
    - close 차분으로 생기는 log_return 중복 컬럼 제거
    - 첫 행(NaN) 제거 후 반환
    """
    df = df.copy()
    target_cols = [c for c in _LOG_DIFF_COLS if c in df.columns]

    for col in target_cols:
        df[col] = np.log(df[col] / df[col].shift(1))

    if "log_return" in df.columns:
        df = df.drop(columns=["log_return"])

    df = df.iloc[1:]
    logger.info("로그 차분 완료: %d개 컬럼 적용, 잔여 %d행", len(target_cols), len(df))
    return df


def minmax_scale(df: pd.DataFrame) -> pd.DataFrame:
    """전체 컬럼에 Min-Max 스케일링 적용 (0~1 범위).

    index·columns 유지한 DataFrame 반환.
    """
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df)
    df_scaled = pd.DataFrame(scaled, index=df.index, columns=df.columns)
    logger.info("MinMax 스케일링 완료: %s", df_scaled.shape)
    return df_scaled
