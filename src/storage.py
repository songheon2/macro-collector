import logging
from pathlib import Path

import pandas as pd

import config

logger = logging.getLogger(__name__)


def _ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_raw(df: pd.DataFrame, name: str) -> None:
    """원본 데이터를 CSV + Parquet 이중 저장."""
    _save(df, name, config.RAW_DIR)


def save_processed(df: pd.DataFrame, name: str) -> None:
    """전처리 완료 데이터를 CSV + Parquet 이중 저장."""
    _save(df, name, config.PROC_DIR)


def _save(df: pd.DataFrame, name: str, base_dir: str) -> None:
    out = _ensure_dir(base_dir)

    parquet_path = out / f"{name}.parquet"
    csv_path = out / f"{name}.csv"

    df.to_parquet(parquet_path, index=True)
    df.to_csv(csv_path, index=True)

    logger.info("저장 완료: %s (parquet: %d 행, %d 컬럼)", name, len(df), len(df.columns))


def load_raw(name: str) -> pd.DataFrame:
    path = Path(config.RAW_DIR) / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"파일 없음: {path}")
    df = pd.read_parquet(path)
    logger.info("로드 완료: %s (%d 행)", name, len(df))
    return df


def load_processed(name: str) -> pd.DataFrame:
    path = Path(config.PROC_DIR) / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"파일 없음: {path}")
    df = pd.read_parquet(path)
    logger.info("로드 완료: %s (%d 행)", name, len(df))
    return df
