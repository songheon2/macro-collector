import logging
import sys

import config
from src.loaders.manual_loader import load_all_manual
from src.storage import save_raw

logger = logging.getLogger(__name__)


def run_load_manual() -> None:
    logger.info("수동 CSV 로드 시작 (inputs/ → outputs/raw/)")

    data = load_all_manual()

    if not data:
        logger.warning("로드된 수동 데이터 없음. inputs/ 디렉토리를 확인하세요.")
        return

    for category, df in data.items():
        save_raw(df, f"{category}_raw")

    logger.info("수동 CSV 로드 완료. 저장 카테고리: %s", list(data.keys()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_load_manual()
