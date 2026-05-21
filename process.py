import logging
import sys
from pathlib import Path

import pandas as pd

import config
from src.preprocessor import mark_holidays, remove_outliers
from src.feature_engineer import calc_log_return, calc_rolling_volatility, calc_yield_spreads
from src.storage import load_raw, save_processed

logger = logging.getLogger(__name__)

_REQUIRED_RAW = ["kospi_ohlcv_raw", "kospi_supply_raw", "bond_raw"]
_OPTIONAL_MANUAL_RAW = ["sentiment_raw", "global_macro_raw", "crypto_raw"]


def _check_raw_files() -> None:
    missing = [
        str(Path(config.RAW_DIR) / f"{name}.parquet")
        for name in _REQUIRED_RAW
        if not (Path(config.RAW_DIR) / f"{name}.parquet").exists()
    ]
    if missing:
        raise RuntimeError(
            f"raw 파일이 없습니다. collect.py를 먼저 실행하세요.\n누락 파일: {missing}"
        )


def run_process() -> None:
    _check_raw_files()
    logger.info("전처리·피처 생성 시작")

    df_kospi = load_raw("kospi_ohlcv_raw")
    df_supply = load_raw("kospi_supply_raw")
    df_bond_all = load_raw("bond_raw")

    manual_frames: list[pd.DataFrame] = []
    for name in _OPTIONAL_MANUAL_RAW:
        path = Path(config.RAW_DIR) / f"{name}.parquet"
        if path.exists():
            manual_frames.append(load_raw(name))
        else:
            logger.warning("수동 데이터 없음, 건너뜀: %s", name)

    # STEP 4: 전처리
    logger.info("=== STEP 4: 전처리 ===")
    df_kospi = mark_holidays(df_kospi)
    df_kospi = remove_outliers(df_kospi)

    df_bond_all = mark_holidays(df_bond_all)
    df_bond_all = remove_outliers(df_bond_all)

    if not df_supply.empty:
        df_supply = mark_holidays(df_supply)
    else:
        logger.warning("supply 데이터 없음 - 전처리 건너뜀")

    processed_manual: list[pd.DataFrame] = []
    for df_m in manual_frames:
        df_m = remove_outliers(df_m)
        processed_manual.append(df_m)

    # STEP 5: 파생변수 생성
    logger.info("=== STEP 5: 파생변수 생성 ===")
    df_kospi = calc_log_return(df_kospi)
    df_kospi = calc_rolling_volatility(df_kospi)
    df_bond_all = calc_yield_spreads(df_bond_all)

    # STEP 6: 통합 저장
    logger.info("=== STEP 6: 통합 저장 ===")
    if df_supply.empty:
        logger.warning(
            "supply 데이터 없음 - 최종 피처에서 컬럼 누락: foreign_net, institution_net, retail_net"
        )
    df_all = pd.concat([df_kospi, df_supply, df_bond_all, *processed_manual], axis=1)
    df_all.index.name = "date"
    save_processed(df_all, "macro_features")

    logger.info("전처리·피처 생성 완료. 최종 shape: %s", df_all.shape)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_process()
