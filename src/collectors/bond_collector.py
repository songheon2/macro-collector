import logging
from typing import Any

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)


def _ecos_url(stat_code: str, cycle: str, start: str, end: str, item_code: str, max_rows: int = 10000) -> str:
    """ECOS StatisticSearch URL 조립."""
    start_d = start.replace("-", "")
    end_d = end.replace("-", "")
    return (
        f"{config.ECOS_BASE_URL}/StatisticSearch"
        f"/{config.ECOS_API_KEY}/json/kr/1/{max_rows}"
        f"/{stat_code}/{cycle}/{start_d}/{end_d}/{item_code}"
    )


@retry(stop=stop_after_attempt(config.RETRY_ATTEMPTS), wait=wait_fixed(config.RETRY_WAIT_SECONDS))
def _fetch_ecos_series(stat_code: str, item_code: str, start: str, end: str, cycle: str = "D") -> pd.Series:
    """ECOS API에서 단일 시계열을 가져와 pd.Series로 반환."""
    url = _ecos_url(stat_code, cycle, start, end, item_code)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    body: dict[str, Any] = resp.json()

    if "StatisticSearch" not in body:
        error_msg = body.get("RESULT", {}).get("MESSAGE", str(body))
        raise RuntimeError(f"ECOS API 오류 [{stat_code}/{item_code}]: {error_msg}")

    rows: list[dict] = body["StatisticSearch"].get("row", [])
    if not rows:
        logger.warning("ECOS 응답 데이터 없음: stat=%s item=%s", stat_code, item_code)
        return pd.Series(dtype=float, name=item_code)

    dates = pd.to_datetime([r["TIME"] for r in rows], format="%Y%m%d")
    values = pd.to_numeric([r["DATA_VALUE"] for r in rows], errors="coerce")
    return pd.Series(values.tolist(), index=dates, name=item_code, dtype=float)


def fetch_bond_yields(start: str, end: str) -> pd.DataFrame:
    """국고채(1Y~30Y) 및 통안채(91D/1Y/2Y) 수익률 수집."""
    logger.info("채권 수익률 수집 시작: %s ~ %s", start, end)

    if not config.ECOS_API_KEY:
        raise ValueError("ECOS_API_KEY가 설정되지 않았습니다. config.py 또는 환경변수를 확인하세요.")

    gov_keys = ["gov_1y", "gov_3y", "gov_5y", "gov_10y", "gov_20y", "gov_30y"]
    msc_keys = ["msc_91d", "msc_1y", "msc_2y"]
    target_keys = gov_keys + msc_keys

    series_list: list[pd.Series] = []
    for key in target_keys:
        item_code = config.ECOS_BOND_ITEMS[key]
        try:
            s = _fetch_ecos_series(config.ECOS_STAT_CODE_BOND, item_code, start, end)
            s.name = key
            series_list.append(s)
            logger.debug("수집 완료: %s (%d건)", key, len(s))
        except Exception as exc:
            logger.error("수집 실패: %s -%s", key, exc)
            raise

    df = pd.concat(series_list, axis=1)
    df.index.name = "date"
    logger.info("채권 수익률 수집 완료: %d 행, %d 컬럼", len(df), len(df.columns))
    return df


def fetch_credit_yields(start: str, end: str) -> pd.DataFrame:
    """회사채 AA- / BBB- 수익률 수집."""
    logger.info("회사채 수익률 수집 시작: %s ~ %s", start, end)

    if not config.ECOS_API_KEY:
        raise ValueError("ECOS_API_KEY가 설정되지 않았습니다.")

    credit_keys = ["corp_aa", "corp_bbb"]
    series_list: list[pd.Series] = []
    for key in credit_keys:
        item_code = config.ECOS_BOND_ITEMS[key]
        try:
            s = _fetch_ecos_series(config.ECOS_STAT_CODE_BOND, item_code, start, end)
            s.name = key
            series_list.append(s)
        except Exception as exc:
            logger.error("회사채 수집 실패: %s -%s", key, exc)
            raise

    df = pd.concat(series_list, axis=1)
    df.index.name = "date"
    logger.info("회사채 수익률 수집 완료: %d 행", len(df))
    return df


def fetch_base_rate(start: str, end: str) -> pd.DataFrame:
    """한국은행 기준금리 수집."""
    logger.info("기준금리 수집 시작: %s ~ %s", start, end)

    if not config.ECOS_API_KEY:
        raise ValueError("ECOS_API_KEY가 설정되지 않았습니다.")

    # 기준금리는 결정일에만 값이 존재 → 일별 reindex는 전처리 단계에서 처리
    s = _fetch_ecos_series(
        config.ECOS_STAT_CODE_BASE_RATE,
        config.ECOS_BASE_RATE_ITEM,
        start,
        end,
        cycle="D",
    )
    s.name = "base_rate"

    df = s.to_frame()
    df.index.name = "date"
    logger.info("기준금리 수집 완료: %d 행", len(df))
    return df
