import logging
import sys

import config
from src.loaders.manual_loader import load_bond, load_all_manual
from src.storage import save_raw

logger = logging.getLogger(__name__)


def run_load_manual() -> None:
    logger.info("수동 CSV 로드 시작 (inputs/ → outputs/raw/)")

    # STEP 1: 채권 수익률 (process.py 선행 필수)
    df_bond = load_bond()
    if df_bond is not None:
        save_raw(df_bond, "bond_raw")
    else:
        logger.warning("채권 데이터 없음 — inputs/bond/ 디렉토리를 확인하세요.")

    # STEP 2: 나머지 수동 데이터 (sentiment / global_macro / crypto)
    data = load_all_manual()
    non_bond = {k: v for k, v in data.items() if k != "bond"}
    for category, df in non_bond.items():
        save_raw(df, f"{category}_raw")

    logger.info("수동 CSV 로드 완료. 저장 카테고리: %s", ["bond"] + list(non_bond.keys()) if df_bond is not None else list(non_bond.keys()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_load_manual()
