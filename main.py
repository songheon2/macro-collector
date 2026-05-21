import logging
import sys

from collect import run_collect
from process import run_process

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger.info("=== 전체 파이프라인 시작 ===")
    run_collect()
    run_process()
    logger.info("=== 전체 파이프라인 완료 ===")
