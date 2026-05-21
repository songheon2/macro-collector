import logging
from pathlib import Path
from typing import Optional

import pandas as pd

import config

logger = logging.getLogger(__name__)

# inputs/ 하위 카테고리별 기대 컬럼 정의
_EXPECTED_COLUMNS: dict[str, list[str]] = {
    "sentiment":    ["date", "sentiment_youtube", "sentiment_news"],
    "global_macro": ["date", "usd_krw", "gold_usd", "nasdaq_close", "us_rate"],
    "crypto":       ["date", "btc_close", "eth_close"],
}

_INPUTS_DIR = Path("inputs")

_COLUMN_MAP: dict[str, dict[str, str]] = {
    "upbit_btc_2021_2025.csv":          {"datetime": "date", "close": "btc_close"},
    "upbit_eth_2021_2025.csv":          {"datetime": "date", "close": "eth_close"},
    "exchange_rate_usdkrw_5years.csv":  {"Date": "date", "USDKRW": "usd_krw"},
    "gold_5years.csv":                  {"Date": "date", "GOLD": "gold_usd"},
    "nasdaq_2021_2025.csv":             {"Price": "date", "Close": "nasdaq_close"},
    "us_10yr_treasury_2021_2025.csv":   {"Price": "date", "Close": "us_rate"},
}

_SKIP_ROWS: dict[str, list[int]] = {
    "nasdaq_2021_2025.csv":           [1, 2],
    "us_10yr_treasury_2021_2025.csv": [1, 2],
}


def _read_csv_auto(path: Path, skip_rows: list[int] | None = None) -> pd.DataFrame:
    """인코딩을 자동 감지해 CSV를 읽는다."""
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=enc, skiprows=skip_rows)
        except (UnicodeDecodeError, ValueError):
            continue
    raise ValueError(f"지원하는 인코딩으로 읽기 실패: {path}")


def _normalize(df: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    """date 컬럼을 DatetimeIndex로 변환하고 인덱스로 설정한다."""
    if "date" not in df.columns:
        raise ValueError(f"'date' 컬럼 없음: {source_path}")

    df = df.copy()
    df = df.set_index(pd.to_datetime(df["date"]).dt.normalize())
    df.index.name = "date"
    df = df.drop(columns=["date"])
    return df


def _validate_columns(df: pd.DataFrame, category: str, path: Path) -> None:
    expected = set(_EXPECTED_COLUMNS.get(category, [])) - {"date"}
    actual = set(df.columns)
    missing = expected - actual
    extra = actual - expected
    if missing:
        logger.warning("[%s] 기대 컬럼 누락 %s: %s", category, path.name, sorted(missing))
    if extra:
        logger.warning("[%s] 예상 외 컬럼 포함 %s: %s", category, path.name, sorted(extra))


def load_category(category: str) -> Optional[pd.DataFrame]:
    """inputs/<category>/ 아래 모든 CSV를 읽어 병합 후 반환한다.

    파일이 없으면 None을 반환한다.
    """
    cat_dir = _INPUTS_DIR / category
    if not cat_dir.exists():
        logger.warning("디렉토리 없음, 스킵: %s", cat_dir)
        return None

    csv_files = sorted(cat_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("CSV 파일 없음, 스킵: %s", cat_dir)
        return None

    frames: list[pd.DataFrame] = []
    expected_cols = set(_EXPECTED_COLUMNS.get(category, [])) - {"date"}

    for path in csv_files:
        try:
            df = _read_csv_auto(path, skip_rows=_SKIP_ROWS.get(path.name))
            df = df.rename(columns=_COLUMN_MAP.get(path.name, {}))
            df = _normalize(df, path)
            drop_cols = [c for c in df.columns if c not in expected_cols]
            if drop_cols:
                df = df.drop(columns=drop_cols)
            frames.append(df)
            logger.info("로드 완료: %s (%d행, %d컬럼)", path.name, len(df), len(df.columns))
        except Exception as exc:
            logger.error("로드 실패 %s: %s", path.name, exc)

    if not frames:
        return None

    combined = frames[0]
    for other in frames[1:]:
        combined = combined.join(other, how="outer", rsuffix="_dup")
        dup_cols = [c for c in combined.columns if c.endswith("_dup")]
        if dup_cols:
            logger.warning("중복 컬럼 발생, 우선 컬럼 유지: %s", dup_cols)
            combined = combined.drop(columns=dup_cols)

    _validate_columns(combined, category, cat_dir)
    return combined


def load_all_manual() -> dict[str, pd.DataFrame]:
    """모든 카테고리를 로드해 {category: DataFrame} 딕셔너리로 반환한다."""
    result: dict[str, pd.DataFrame] = {}
    for category in _EXPECTED_COLUMNS:
        df = load_category(category)
        if df is not None:
            result[category] = df
            logger.info("카테고리 완료: %s → %d행 %d컬럼", category, len(df), len(df.columns))
        else:
            logger.warning("카테고리 데이터 없음: %s", category)
    return result
