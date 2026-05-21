import logging

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


def mark_holidays(df: pd.DataFrame) -> pd.DataFrame:
    """영업일 범위에서 데이터가 없는 날(휴장일)을 NaN으로 마킹.

    forward fill 금지: 모델 레이어에서 처리.
    """
    biz_index = pd.bdate_range(start=df.index.min(), end=df.index.max(), freq="B")
    df = df.reindex(biz_index)
    df.index.name = "date"

    holiday_count = df.isnull().all(axis=1).sum()
    logger.info("휴장일 마킹 완료: %d일 NaN 처리", holiday_count)
    return df


def remove_outliers(df: pd.DataFrame, sigma: float = config.OUTLIER_SIGMA) -> pd.DataFrame:
    """수치형 컬럼에서 평균 ± sigma*σ 범위를 벗어난 값을 NaN으로 대체."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df = df.copy()

    total_replaced = 0
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        mask = (df[col] - mean).abs() > sigma * std
        count = mask.sum()
        if count:
            df.loc[mask, col] = np.nan
            total_replaced += count
            logger.debug("이상치 제거: %s — %d건", col, count)

    logger.info("이상치 제거 완료: 총 %d건 NaN 처리 (sigma=%.1f)", total_replaced, sigma)
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """결측치 2단계 처리: 이상치 NaN 보간 → 휴장일 NaN ffill."""
    # 1단계: 이상치 제거로 생긴 고립 NaN — 직전·직후 값으로 선형 보간 (최대 1일)
    df = df.interpolate(method="time", limit=1, limit_direction="both")
    # 2단계: 휴장일·주말 NaN — forward fill
    df = df.ffill()
    remaining = df.isnull().sum().sum()
    logger.info("결측 처리 완료 (보간→ffill). 잔여 결측: %d셀 (시작부 선행값 없음)", remaining)
    return df


def align_dates(df_left: pd.DataFrame, df_right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """두 DataFrame을 공통 날짜 인덱스로 정렬."""
    common = df_left.index.intersection(df_right.index)
    logger.info("공통 날짜 수: %d", len(common))
    return df_left.reindex(common), df_right.reindex(common)
