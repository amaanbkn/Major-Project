"""
FinSight AI — IPO Tracker Service
Scrapes IPO calendar, GMP (Grey Market Premium) data from web sources.
Sources: BSE IPO listings + investorgain.com/chittorgarh via BeautifulSoup.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

# ── In-memory cache ─────────────────────────────────────────
_ipo_cache: dict = {"data": None, "timestamp": None}
_gmp_cache: dict = {"data": None, "timestamp": None}
CACHE_TTL = timedelta(minutes=30)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


async def get_upcoming_ipos() -> list[dict]:
    """
    Fetch upcoming and current IPO listings.
    Returns list of IPOs with dates, price band, lot size, etc.
    """
    global _ipo_cache

    # Check cache
    if (
        _ipo_cache["data"] is not None
        and _ipo_cache["timestamp"]
        and (datetime.now() - _ipo_cache["timestamp"]) < CACHE_TTL
    ):
        return _ipo_cache["data"]

    ipos = []

    try:
        async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
            # Try investorgain.com for IPO data
            response = await client.get("https://www.investorgain.com/report/live-ipo-gmp/331/")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.find("table", {"id": "mainTable"})

                if table:
                    rows = table.find_all("tr")[1:]  # Skip header row
                    for row in rows[:20]:  # Limit to 20 IPOs
                        cols = row.find_all("td")
                        if len(cols) >= 5:
                            name = cols[0].get_text(strip=True)
                            price = cols[1].get_text(strip=True) if len(cols) > 1 else "N/A"
                            gmp = cols[2].get_text(strip=True) if len(cols) > 2 else "N/A"
                            lot_size = cols[3].get_text(strip=True) if len(cols) > 3 else "N/A"
                            open_date = cols[4].get_text(strip=True) if len(cols) > 4 else "N/A"
                            close_date = cols[5].get_text(strip=True) if len(cols) > 5 else "N/A"

                            ipos.append({
                                "name": name,
                                "price_band": price,
                                "gmp": gmp,
                                "lot_size": lot_size,
                                "open_date": open_date,
                                "close_date": close_date,
                                "source": "investorgain",
                            })

    except Exception as e:
        logger.error(f"IPO scraping error (investorgain): {e}")

    # Fallback: Try Chittorgarh
    if not ipos:
        try:
            async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
                response = await client.get("https://www.chittorgarh.com/report/mainboard-ipo-list-in-india-702/1/")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    table = soup.find("table", class_="table")

                    if table:
                        rows = table.find_all("tr")[1:]
                        for row in rows[:15]:
                            cols = row.find_all("td")
                            if len(cols) >= 4:
                                ipos.append({
                                    "name": cols[0].get_text(strip=True),
                                    "open_date": cols[1].get_text(strip=True) if len(cols) > 1 else "N/A",
                                    "close_date": cols[2].get_text(strip=True) if len(cols) > 2 else "N/A",
                                    "price_band": cols[3].get_text(strip=True) if len(cols) > 3 else "N/A",
                                    "lot_size": cols[4].get_text(strip=True) if len(cols) > 4 else "N/A",
                                    "gmp": "N/A",
                                    "source": "chittorgarh",
                                })
        except Exception as e:
            logger.error(f"IPO scraping error (chittorgarh): {e}")

    # If both scrapers failed, return sample data for demonstration
    if not ipos:
        logger.warning("Both IPO scrapers failed. Returning demo data.")
        ipos = _get_demo_ipo_data()

    _ipo_cache = {"data": ipos, "timestamp": datetime.now()}
    logger.info(f"✅ Fetched {len(ipos)} IPO listings")
    return ipos


async def get_ipo_gmp() -> list[dict]:
    """
    Fetch Grey Market Premium data for current IPOs.
    """
    global _gmp_cache

    if (
        _gmp_cache["data"] is not None
        and _gmp_cache["timestamp"]
        and (datetime.now() - _gmp_cache["timestamp"]) < CACHE_TTL
    ):
        return _gmp_cache["data"]

    # GMP data is already included in get_upcoming_ipos
    ipos = await get_upcoming_ipos()
    gmp_data = [
        {
            "name": ipo["name"],
            "price_band": ipo["price_band"],
            "gmp": ipo.get("gmp", "N/A"),
        }
        for ipo in ipos
        if ipo.get("gmp") and ipo["gmp"] != "N/A"
    ]

    _gmp_cache = {"data": gmp_data, "timestamp": datetime.now()}
    return gmp_data


def _get_demo_ipo_data() -> list[dict]:
    """Fallback demo IPO data when scrapers fail."""
    return [
        {
            "name": "Demo IPO (Scraper Unavailable)",
            "price_band": "₹100 - ₹120",
            "gmp": "+₹25",
            "lot_size": "125",
            "open_date": "TBA",
            "close_date": "TBA",
            "source": "demo",
            "note": "Live data temporarily unavailable. Please try again later.",
        }
    ]


def clear_ipo_cache():
    """Clear IPO caches (called by scheduler after refresh)."""
    global _ipo_cache, _gmp_cache
    _ipo_cache = {"data": None, "timestamp": None}
    _gmp_cache = {"data": None, "timestamp": None}
    logger.info("🗑️ IPO cache cleared")
