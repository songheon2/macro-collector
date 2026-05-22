import logging
import sys
from pathlib import Path

import config
from src.scaler import log_diff_prices, minmax_scale
from src.storage import load_processed, save_processed

logger = logging.getLogger(__name__)


def _check_processed_file() -> None:
    path = Path(config.PROC_DIR) / "macro_features.parquet"
    if not path.exists():
        raise RuntimeError(
            f"전처리 파일이 없습니다. process.py를 먼저 실행하세요.\n누락 파일: {path}"
        )


def run_scale() -> None:
    _check_processed_file()
    logger.info("스케일링 시작")

    df = load_processed("macro_features")

    logger.info("=== STEP 1: 로그 차분 ===")
    df = log_diff_prices(df)

    logger.info("=== STEP 2: MinMax 스케일링 ===")
    df = minmax_scale(df)

    save_processed(df, "macro_features_scaled")
    logger.info("스케일링 완료. 최종 shape: %s", df.shape)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_scale()
