import logging
import sys

import pandas as pd

import config
from src.collectors.kospi_collector import fetch_kospi_ohlcv, fetch_kospi_supply
from src.collectors.bond_collector import fetch_bond_yields, fetch_credit_yields, fetch_base_rate
from src.collectors.supplement_collector import fetch_kospi_yfinance, merge_with_fallback
from src.storage import save_raw

logger = logging.getLogger(__name__)


def run_collect() -> None:
    start = config.START_DATE
    end = config.END_DATE
    logger.info("수집 시작: %s ~ %s", start, end)

    # STEP 1: KOSPI OHLCV + yfinance fallback
    logger.info("=== STEP 1: KOSPI OHLCV 수집 ===")
    df_kospi = fetch_kospi_ohlcv(start, end)
    df_yf = fetch_kospi_yfinance(start, end)
    df_kospi = merge_with_fallback(df_kospi, df_yf)
    save_raw(df_kospi, "kospi_ohlcv_raw")

    # STEP 2: KOSPI 수급 (pykrx KRX API 실패 시 빈 DataFrame 저장 후 계속)
    logger.info("=== STEP 2: KOSPI 수급 수집 ===")
    try:
        df_supply = fetch_kospi_supply(start, end)
    except Exception as exc:
        logger.error(
            "[STEP 2 실패] KOSPI 수급 수집 불가 - KRX API 접근 오류. "
            "빈 DataFrame으로 저장 후 계속합니다. 원인: %s", exc
        )
        df_supply = pd.DataFrame()
    save_raw(df_supply, "kospi_supply_raw")

    # STEP 3: 채권 수익률
    logger.info("=== STEP 3: 채권 수익률 수집 ===")
    df_bond = fetch_bond_yields(start, end)
    df_credit = fetch_credit_yields(start, end)
    df_base = fetch_base_rate(start, end)
    df_bond_all = pd.concat([df_bond, df_credit, df_base], axis=1)
    save_raw(df_bond_all, "bond_raw")

    logger.info("수집 완료")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_collect()
