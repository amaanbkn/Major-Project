"""
FinSight AI — IPO Tracker Service

Fetches Indian IPO information from public web sources.

Primary source:
    InvestorGain — live IPO GMP information

Secondary source:
    Chittorgarh — mainboard IPO information

The service:
- Uses asynchronous HTTP requests
- Parses public HTML using BeautifulSoup
- Normalizes IPO records
- Adds active/upcoming/closed status
- Caches results for 30 minutes
- NEVER returns fabricated/demo financial data
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup
from loguru import logger


# ============================================================
# Configuration
# ============================================================

IST = ZoneInfo("Asia/Kolkata")

CACHE_TTL = timedelta(minutes=30)

INVESTORGAIN_URL = (
    "https://www.investorgain.com/report/live-ipo-gmp/331/"
)

CHITTORGARH_URL = (
    "https://www.chittorgarh.com/report/"
    "mainboard-ipo-list-in-india-702/1/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Cache-Control": "no-cache",
}


# ============================================================
# Cache
# ============================================================

_ipo_cache: dict[str, Any] = {
    "data": None,
    "timestamp": None,
}


# ============================================================
# Helpers
# ============================================================

def _now() -> datetime:
    """Current India Standard Time."""
    return datetime.now(IST)


def _clean_text(value: str | None) -> str:
    """Normalize scraped text."""
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def _extract_date(value: str | None) -> str | None:
    """
    Extract a date from scraped text.

    Returns original cleaned text when a formal date cannot be
    confidently parsed. This avoids silently inventing dates.
    """
    value = _clean_text(value)

    if not value:
        return None

    patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}",
        r"[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            return match.group(0)

    return value


def _parse_date_for_status(value: str | None) -> datetime | None:
    """Best-effort parsing for determining IPO status."""
    if not value:
        return None

    value = _clean_text(value)

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(
                value,
                fmt,
            )

            return parsed.replace(
                tzinfo=IST
            )
        except ValueError:
            continue

    return None


def _calculate_status(
    open_date: str | None,
    close_date: str | None,
) -> str:
    """
    Determine whether an IPO is upcoming, active, or closed.

    If dates cannot be parsed confidently, return 'unknown'
    rather than guessing.
    """

    now = _now()

    opening = _parse_date_for_status(open_date)
    closing = _parse_date_for_status(close_date)

    if opening and now < opening:
        return "upcoming"

    if opening and closing:
        if opening <= now <= closing:
            return "active"

        if now > closing:
            return "closed"

    if closing and now <= closing:
        return "active"

    return "unknown"


def _normalize_gmp(value: str | None) -> str:
    """Normalize GMP display without inventing numerical values."""
    value = _clean_text(value)

    if not value:
        return "N/A"

    return value


def _normalize_price_band(value: str | None) -> str:
    """Normalize price band text."""
    value = _clean_text(value)

    if not value:
        return "N/A"

    return value


# ============================================================
# InvestorGain scraper
# ============================================================

async def _fetch_investorgain() -> list[dict]:
    """
    Fetch IPO and GMP information from InvestorGain.
    """

    logger.info(
        "Fetching IPO data from InvestorGain..."
    )

    ipos: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:

            response = await client.get(
                INVESTORGAIN_URL
            )

            response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # Prefer the known table ID, but fall back to the
        # first useful table if the website structure changes.
        table = soup.find(
            "table",
            id="mainTable",
        )

        if table is None:
            tables = soup.find_all("table")

            table = (
                tables[0]
                if tables
                else None
            )

        if table is None:
            logger.warning(
                "InvestorGain page loaded but no table was found."
            )
            return []

        rows = table.find_all("tr")

        for row in rows[1:]:
            cells = row.find_all(
                ["td", "th"]
            )

            values = [
                _clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
                for cell in cells
            ]

            # Ignore malformed rows.
            if len(values) < 3:
                continue

            name = values[0]

            if not name:
                continue

            # InvestorGain tables can change column ordering.
            # We keep the values conservatively rather than
            # inventing semantics for unknown columns.
            price_band = (
                values[1]
                if len(values) > 1
                else "N/A"
            )

            gmp = (
                values[2]
                if len(values) > 2
                else "N/A"
            )

            lot_size = (
                values[3]
                if len(values) > 3
                else "N/A"
            )

            open_date = (
                _extract_date(values[4])
                if len(values) > 4
                else None
            )

            close_date = (
                _extract_date(values[5])
                if len(values) > 5
                else None
            )

            status = _calculate_status(
                open_date,
                close_date,
            )

            ipos.append(
                {
                    "name": name,
                    "price_band": _normalize_price_band(
                        price_band
                    ),
                    "gmp": _normalize_gmp(
                        gmp
                    ),
                    "lot_size": (
                        lot_size or "N/A"
                    ),
                    "open_date": (
                        open_date or "N/A"
                    ),
                    "close_date": (
                        close_date or "N/A"
                    ),
                    "status": status,
                    "source": "InvestorGain",
                }
            )

            if len(ipos) >= 20:
                break

        logger.info(
            f"InvestorGain returned "
            f"{len(ipos)} IPO records."
        )

        return ipos

    except httpx.HTTPStatusError as exc:
        logger.error(
            f"InvestorGain HTTP error: "
            f"{exc.response.status_code}"
        )

    except httpx.RequestError as exc:
        logger.error(
            f"InvestorGain network error: {exc}"
        )

    except Exception as exc:
        logger.exception(
            f"InvestorGain scraping failed: {exc}"
        )

    return []


# ============================================================
# Chittorgarh scraper
# ============================================================

async def _fetch_chittorgarh() -> list[dict]:
    """
    Fetch mainboard IPO information from Chittorgarh.

    Used as a secondary source when InvestorGain does not
    provide usable IPO records.
    """

    logger.info(
        "Fetching IPO data from Chittorgarh..."
    )

    ipos: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:

            response = await client.get(
                CHITTORGARH_URL
            )

            response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        tables = soup.find_all(
            "table"
        )

        if not tables:
            logger.warning(
                "Chittorgarh page loaded but no table was found."
            )
            return []

        # Select the first table with at least 4 columns.
        selected_table = None

        for candidate in tables:

            rows = candidate.find_all("tr")

            if not rows:
                continue

            first_data_row = rows[1] if len(rows) > 1 else None

            if first_data_row:
                cells = first_data_row.find_all(
                    ["td", "th"]
                )

                if len(cells) >= 4:
                    selected_table = candidate
                    break

        if selected_table is None:
            return []

        rows = selected_table.find_all(
            "tr"
        )

        for row in rows[1:]:

            cells = row.find_all(
                ["td", "th"]
            )

            values = [
                _clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
                for cell in cells
            ]

            if len(values) < 4:
                continue

            name = values[0]

            if not name:
                continue

            open_date = (
                _extract_date(values[1])
                if len(values) > 1
                else None
            )

            close_date = (
                _extract_date(values[2])
                if len(values) > 2
                else None
            )

            price_band = (
                values[3]
                if len(values) > 3
                else "N/A"
            )

            lot_size = (
                values[4]
                if len(values) > 4
                else "N/A"
            )

            status = _calculate_status(
                open_date,
                close_date,
            )

            ipos.append(
                {
                    "name": name,
                    "price_band": _normalize_price_band(
                        price_band
                    ),
                    "gmp": "N/A",
                    "lot_size": (
                        lot_size or "N/A"
                    ),
                    "open_date": (
                        open_date or "N/A"
                    ),
                    "close_date": (
                        close_date or "N/A"
                    ),
                    "status": status,
                    "source": "Chittorgarh",
                }
            )

            if len(ipos) >= 20:
                break

        logger.info(
            f"Chittorgarh returned "
            f"{len(ipos)} IPO records."
        )

        return ipos

    except httpx.HTTPStatusError as exc:
        logger.error(
            f"Chittorgarh HTTP error: "
            f"{exc.response.status_code}"
        )

    except httpx.RequestError as exc:
        logger.error(
            f"Chittorgarh network error: {exc}"
        )

    except Exception as exc:
        logger.exception(
            f"Chittorgarh scraping failed: {exc}"
        )

    return []


# ============================================================
# Public IPO API
# ============================================================

async def get_upcoming_ipos() -> list[dict]:
    """
    Return currently relevant IPO records.

    The service tries InvestorGain first, then Chittorgarh.

    IMPORTANT:
    No demo or fabricated financial data is returned.
    """

    global _ipo_cache

    now = _now()

    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    if (
        _ipo_cache["data"] is not None
        and _ipo_cache["timestamp"] is not None
    ):

        age = (
            now - _ipo_cache["timestamp"]
        )

        if age < CACHE_TTL:

            logger.debug(
                f"Using cached IPO data "
                f"(age={age})."
            )

            return _ipo_cache["data"]

    # --------------------------------------------------------
    # Primary source
    # --------------------------------------------------------

    ipos = await _fetch_investorgain()

    # --------------------------------------------------------
    # Secondary source
    # --------------------------------------------------------

    if not ipos:
        logger.warning(
            "InvestorGain returned no IPO data. "
            "Trying Chittorgarh."
        )

        ipos = await _fetch_chittorgarh()

    # --------------------------------------------------------
    # No data
    # --------------------------------------------------------

    if not ipos:

        logger.error(
            "All IPO sources failed. "
            "Returning an empty dataset."
        )

        # Do NOT return demo financial information.
        _ipo_cache = {
            "data": [],
            "timestamp": now,
        }

        return []

    # --------------------------------------------------------
    # Sort:
    # active → upcoming → unknown → closed
    # --------------------------------------------------------

    status_priority = {
        "active": 0,
        "upcoming": 1,
        "unknown": 2,
        "closed": 3,
    }

    ipos.sort(
        key=lambda item: (
            status_priority.get(
                item.get("status"),
                99,
            ),
            item.get(
                "open_date",
                "",
            ),
        )
    )

    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    _ipo_cache = {
        "data": ipos,
        "timestamp": now,
    }

    logger.info(
        f"✅ IPO tracker updated: "
        f"{len(ipos)} records"
    )

    return ipos


# ============================================================
# GMP API
# ============================================================

async def get_ipo_gmp() -> list[dict]:
    """
    Return IPO GMP information from the IPO dataset.
    """

    ipos = await get_upcoming_ipos()

    return [
        {
            "name": ipo.get(
                "name",
                "N/A",
            ),
            "price_band": ipo.get(
                "price_band",
                "N/A",
            ),
            "gmp": ipo.get(
                "gmp",
                "N/A",
            ),
            "status": ipo.get(
                "status",
                "unknown",
            ),
            "source": ipo.get(
                "source",
                "unknown",
            ),
        }
        for ipo in ipos
        if ipo.get("gmp")
        and ipo.get("gmp") != "N/A"
    ]


# ============================================================
# Cache Management
# ============================================================

def clear_ipo_cache() -> None:
    """Clear IPO cache for scheduler/manual refresh."""
    global _ipo_cache

    _ipo_cache = {
        "data": None,
        "timestamp": None,
    }

    logger.info(
        "🗑️ IPO cache cleared."
    )