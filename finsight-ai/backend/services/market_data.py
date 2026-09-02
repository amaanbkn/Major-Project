"""
FinSight AI — Market Data Service

Provides:
- Live/latest stock prices via yfinance
- Historical OHLCV data
- Company information
- NIFTY 50 constituent snapshot
- NIFTY 50 index data

The service is designed for asynchronous FastAPI usage by
moving blocking yfinance operations into worker threads.

Important:
If a data source fails, this module returns an explicit
error/unavailable state instead of fabricated financial values.
"""

from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf
from loguru import logger


# ============================================================
# Configuration
# ============================================================

IST = ZoneInfo("Asia/Kolkata")

MARKET_CACHE_TTL = timedelta(minutes=15)
NIFTY_CACHE_TTL = timedelta(minutes=15)


# ============================================================
# Caches
# ============================================================

_stock_cache: dict[str, dict[str, Any]] = {}

_nifty_snapshot_cache: dict[str, Any] = {
    "data": None,
    "timestamp": None,
}

_nifty_index_cache: dict[str, Any] = {
    "data": None,
    "timestamp": None,
}


# ============================================================
# NIFTY 50 Constituents
# ============================================================

NIFTY_50_SYMBOLS = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "ITC",
    "SBIN",
    "BAJFINANCE",
    "BHARTIARTL",
    "KOTAKBANK",
    "LT",
    "HCLTECH",
    "AXISBANK",
    "ASIANPAINT",
    "MARUTI",
    "SUNPHARMA",
    "TITAN",
    "ULTRACEMCO",
    "BAJAJFINSV",
    "WIPRO",
    "NESTLEIND",
    "NTPC",
    "TECHM",
    "POWERGRID",
    "TATAMOTORS",
    "M&M",
    "JSWSTEEL",
    "ADANIENT",
    "ADANIPORTS",
    "TATASTEEL",
    "ONGC",
    "HDFCLIFE",
    "DIVISLAB",
    "SBILIFE",
    "BAJAJ-AUTO",
    "GRASIM",
    "CIPLA",
    "APOLLOHOSP",
    "DRREDDY",
    "COALINDIA",
    "BPCL",
    "BRITANNIA",
    "EICHERMOT",
    "TATACONSUM",
    "HEROMOTOCO",
    "INDUSINDBK",
    "UPL",
    "BEL",
    "TRENT",
]


# ============================================================
# Helpers
# ============================================================

def _now() -> datetime:
    """Current India Standard Time."""
    return datetime.now(IST)


def _nse_symbol(symbol: str) -> str:
    """
    Convert an Indian stock symbol into its Yahoo Finance ticker.
    """

    symbol = str(symbol).strip().upper()

    if not symbol:
        return ""

    if symbol.startswith("^"):
        return symbol

    if symbol.endswith(".NS"):
        return symbol

    return f"{symbol}.NS"


def _display_symbol(symbol: str) -> str:
    """
    Normalize a symbol for API responses.
    """

    return (
        str(symbol)
        .strip()
        .upper()
        .replace(".NS", "")
    )


def _safe_float(
    value: Any,
    default: float | None = None,
) -> float | None:
    """
    Safely convert a value to float.

    Returns None for missing/non-numeric values instead of
    converting unavailable financial data into zero.
    """

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    try:
        numeric = float(value)

        if math.isnan(numeric) or math.isinf(numeric):
            return default

        return numeric

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int | None = None,
) -> int | None:
    """Safely convert a value to integer."""

    numeric = _safe_float(value, None)

    if numeric is None:
        return default

    try:
        return int(numeric)
    except (TypeError, ValueError, OverflowError):
        return default


def _round(
    value: Any,
    digits: int = 2,
) -> float | None:
    """Safely round a numeric value."""

    numeric = _safe_float(value)

    if numeric is None:
        return None

    return round(numeric, digits)


def _cache_valid(
    timestamp: Optional[datetime],
    ttl: timedelta,
) -> bool:
    """Check cache freshness."""

    if timestamp is None:
        return False

    return (_now() - timestamp) < ttl


# ============================================================
# Stock Price
# ============================================================

async def get_stock_price(
    symbol: str,
) -> dict:
    """
    Fetch latest available stock price and basic metrics.
    """

    display_symbol = _display_symbol(symbol)

    if not display_symbol:
        return {
            "symbol": "",
            "status": "error",
            "error": "Stock symbol cannot be empty.",
        }

    cache_key = display_symbol

    cached = _stock_cache.get(cache_key)

    if cached and _cache_valid(
        cached.get("timestamp"),
        MARKET_CACHE_TTL,
    ):
        return cached["data"]

    yahoo_symbol = _nse_symbol(display_symbol)

    logger.info(
        "Fetching stock data: {} ({})",
        display_symbol,
        yahoo_symbol,
    )

    try:
        ticker = yf.Ticker(yahoo_symbol)

        def _fetch() -> tuple[Any, dict]:
            fast_info = None
            info: dict[str, Any] = {}

            try:
                fast_info = ticker.fast_info
            except Exception as exc:
                logger.debug(
                    "fast_info failed for {}: {}",
                    display_symbol,
                    exc,
                )

            try:
                info = ticker.info or {}
            except Exception as exc:
                logger.debug(
                    "ticker.info failed for {}: {}",
                    display_symbol,
                    exc,
                )

            return fast_info, info

        fast_info, info = await asyncio.to_thread(_fetch)

        # ----------------------------------------------------
        # Latest price
        # ----------------------------------------------------

        price_candidates: list[Any] = []

        try:
            if fast_info is not None:
                price_candidates.append(
                    fast_info.get("last_price")
                )
        except Exception:
            pass

        price_candidates.extend(
            [
                info.get("currentPrice"),
                info.get("regularMarketPrice"),
            ]
        )

        price = next(
            (
                value
                for value in price_candidates
                if _safe_float(value) is not None
            ),
            None,
        )

        # ----------------------------------------------------
        # Previous close
        # ----------------------------------------------------

        previous_candidates: list[Any] = []

        try:
            if fast_info is not None:
                previous_candidates.append(
                    fast_info.get("previous_close")
                )
        except Exception:
            pass

        previous_candidates.extend(
            [
                info.get("previousClose"),
                info.get("regularMarketPreviousClose"),
            ]
        )

        previous_close = next(
            (
                value
                for value in previous_candidates
                if _safe_float(value) is not None
            ),
            None,
        )

        price = _safe_float(price)
        previous_close = _safe_float(previous_close)

        # ----------------------------------------------------
        # Change
        # ----------------------------------------------------

        change = None
        change_pct = None

        if (
            price is not None
            and previous_close is not None
            and previous_close != 0
        ):
            change = price - previous_close
            change_pct = (
                change / previous_close
            ) * 100

        # ----------------------------------------------------
        # Volume
        # ----------------------------------------------------

        volume = None

        try:
            if fast_info is not None:
                volume = _safe_int(
                    fast_info.get("last_volume")
                    or fast_info.get("volume")
                )
        except Exception:
            pass

        if volume is None:
            volume = _safe_int(
                info.get("volume")
            )

        # ----------------------------------------------------
        # Other metrics
        # ----------------------------------------------------

        day_high = (
            info.get("dayHigh")
            or info.get("regularMarketDayHigh")
        )

        day_low = (
            info.get("dayLow")
            or info.get("regularMarketDayLow")
        )

        week52_high = info.get(
            "fiftyTwoWeekHigh"
        )

        week52_low = info.get(
            "fiftyTwoWeekLow"
        )

        market_cap = info.get(
            "marketCap"
        )

        pe_ratio = info.get(
            "trailingPE"
        )

        eps = (
            info.get("trailingEps")
            or info.get(
                "epsTrailingTwelveMonths"
            )
        )

        # ----------------------------------------------------
        # Validate actual price
        # ----------------------------------------------------

        if price is None:
            logger.warning(
                "No valid price returned for {}",
                display_symbol,
            )

            return {
                "symbol": display_symbol,
                "status": "unavailable",
                "error": "Current price is unavailable.",
                "timestamp": _now().isoformat(),
                "source": "yfinance",
            }

        result = {
            "symbol": display_symbol,
            "price": _round(price),
            "previous_close": _round(previous_close),
            "change": _round(change),
            "change_pct": _round(change_pct),
            "volume": volume,
            "day_high": _round(day_high),
            "day_low": _round(day_low),
            "52w_high": _round(week52_high),
            "52w_low": _round(week52_low),
            "market_cap": market_cap,
            "pe_ratio": _round(pe_ratio),
            "eps": _round(eps),
            "timestamp": _now().isoformat(),
            "source": "yfinance",
            "status": "success",
        }

        _stock_cache[cache_key] = {
            "data": result,
            "timestamp": _now(),
        }

        return result

    except Exception as exc:
        logger.exception(
            "Error fetching price for {}: {}",
            display_symbol,
            exc,
        )

        return {
            "symbol": display_symbol,
            "status": "error",
            "error": "Unable to retrieve stock data.",
            "timestamp": _now().isoformat(),
            "source": "yfinance",
        }


# ============================================================
# Historical Data
# ============================================================

async def get_stock_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> list[dict]:
    """
    Fetch historical OHLCV data for charts and technical analysis.
    """

    display_symbol = _display_symbol(symbol)

    if not display_symbol:
        return []

    valid_periods = {
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y",
        "10y",
        "max",
    }

    valid_intervals = {
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1h",
        "1d",
        "5d",
        "1wk",
        "1mo",
        "3mo",
    }

    if period not in valid_periods:
        logger.warning(
            "Invalid history period: {}",
            period,
        )
        return []

    if interval not in valid_intervals:
        logger.warning(
            "Invalid history interval: {}",
            interval,
        )
        return []

    try:
        ticker = yf.Ticker(
            _nse_symbol(display_symbol)
        )

        df: pd.DataFrame = await asyncio.to_thread(
            lambda: ticker.history(
                period=period,
                interval=interval,
                auto_adjust=False,
            )
        )

        if df.empty:
            logger.warning(
                "No historical data for {}",
                display_symbol,
            )
            return []

        df = df.reset_index()

        records: list[dict] = []

        for _, row in df.iterrows():
            close = _safe_float(
                row.get("Close")
            )

            if close is None:
                continue

            timestamp = (
                row.get("Datetime")
                if "Datetime" in row
                else row.get("Date")
            )

            if hasattr(timestamp, "isoformat"):
                date_value = timestamp.isoformat()
            else:
                date_value = str(timestamp)

            records.append(
                {
                    "date": date_value,
                    "open": _round(
                        row.get("Open")
                    ),
                    "high": _round(
                        row.get("High")
                    ),
                    "low": _round(
                        row.get("Low")
                    ),
                    "close": _round(close),
                    "volume": _safe_int(
                        row.get("Volume")
                    ),
                }
            )

        return records

    except Exception as exc:
        logger.exception(
            "Error fetching history for {}: {}",
            display_symbol,
            exc,
        )
        return []


# ============================================================
# Company Information
# ============================================================

async def get_company_info(
    symbol: str,
) -> dict:
    """
    Fetch company metadata.
    """

    display_symbol = _display_symbol(symbol)

    if not display_symbol:
        return {
            "symbol": "",
            "status": "error",
            "error": "Stock symbol cannot be empty.",
        }

    try:
        ticker = yf.Ticker(
            _nse_symbol(display_symbol)
        )

        info = await asyncio.to_thread(
            lambda: ticker.info or {}
        )

        return {
            "symbol": display_symbol,
            "name": (
                info.get("longName")
                or info.get("shortName")
                or display_symbol
            ),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get(
                "longBusinessSummary"
            ),
            "website": info.get("website"),
            "employees": _safe_int(
                info.get("fullTimeEmployees")
            ),
            "status": "success",
            "source": "yfinance",
            "timestamp": _now().isoformat(),
        }

    except Exception as exc:
        logger.exception(
            "Error fetching company info for {}: {}",
            display_symbol,
            exc,
        )

        return {
            "symbol": display_symbol,
            "status": "error",
            "error": "Unable to retrieve company information.",
        }


# ============================================================
# NIFTY 50 Constituents
# ============================================================

async def get_nifty50_snapshot() -> list[dict]:
    """
    Return latest available price/change for NIFTY 50 stocks.

    Uses yfinance batch download where possible.
    """

    global _nifty_snapshot_cache

    cached_data = _nifty_snapshot_cache.get("data")
    cached_timestamp = _nifty_snapshot_cache.get("timestamp")

    if (
        cached_data is not None
        and _cache_valid(
            cached_timestamp,
            NIFTY_CACHE_TTL,
        )
    ):
        logger.debug(
            "Returning cached NIFTY 50 snapshot."
        )
        return cached_data

    logger.info(
        "Refreshing NIFTY 50 constituent snapshot..."
    )

    tickers = [
        _nse_symbol(symbol)
        for symbol in NIFTY_50_SYMBOLS
    ]

    try:
        df = await asyncio.to_thread(
            lambda: yf.download(
                tickers=tickers,
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        )

        if df.empty:
            logger.error(
                "NIFTY 50 batch download returned no data."
            )
            return []

        snapshot: list[dict] = []

        for display_symbol in NIFTY_50_SYMBOLS:
            yahoo_symbol = _nse_symbol(
                display_symbol
            )

            try:
                if isinstance(df.columns, pd.MultiIndex):
                    if (
                        yahoo_symbol
                        not in df.columns.get_level_values(0)
                    ):
                        continue

                    ticker_df = df[yahoo_symbol]

                else:
                    ticker_df = df

                if ticker_df.empty:
                    continue

                close_series = (
                    ticker_df["Close"]
                    .dropna()
                )

                if close_series.empty:
                    continue

                latest_price = _safe_float(
                    close_series.iloc[-1]
                )

                if latest_price is None:
                    continue

                previous_close = None

                if len(close_series) >= 2:
                    previous_close = _safe_float(
                        close_series.iloc[-2]
                    )

                change = None
                change_pct = None

                if (
                    previous_close is not None
                    and previous_close != 0
                ):
                    change = (
                        latest_price
                        - previous_close
                    )

                    change_pct = (
                        change
                        / previous_close
                    ) * 100

                snapshot.append(
                    {
                        "symbol": display_symbol,
                        "price": _round(
                            latest_price
                        ),
                        "previous_close": _round(
                            previous_close
                        ),
                        "change": _round(change),
                        "change_pct": _round(
                            change_pct
                        ),
                        "source": "yfinance",
                        "status": "success",
                    }
                )

            except Exception as exc:
                logger.warning(
                    "Skipping {}: {}",
                    display_symbol,
                    exc,
                )

        _nifty_snapshot_cache = {
            "data": snapshot,
            "timestamp": _now(),
        }

        logger.info(
            "✅ NIFTY 50 snapshot refreshed: {} stocks",
            len(snapshot),
        )

        return snapshot

    except Exception as exc:
        logger.exception(
            "NIFTY 50 batch download failed: {}",
            exc,
        )
        return []


# ============================================================
# NIFTY 50 Index
# ============================================================

async def get_nifty_index() -> dict:
    """
    Get the latest NIFTY 50 index value.

    Yahoo Finance ticker:
        ^NSEI

    IMPORTANT:
    Previous close is calculated from the latest two daily
    historical closes whenever possible. This avoids relying
    solely on fast_info/regularMarketPreviousClose, which can
    become stale or inconsistent.
    """

    global _nifty_index_cache

    cached_data = _nifty_index_cache.get("data")
    cached_timestamp = _nifty_index_cache.get("timestamp")

    if (
        cached_data is not None
        and _cache_valid(
            cached_timestamp,
            NIFTY_CACHE_TTL,
        )
    ):
        logger.debug(
            "Returning cached NIFTY 50 index."
        )
        return cached_data

    try:
        ticker = yf.Ticker("^NSEI")

        # ----------------------------------------------------
        # Fetch current metadata + historical closes
        # ----------------------------------------------------

        def _fetch() -> tuple[Any, dict, pd.DataFrame]:
            fast_info = None
            info: dict[str, Any] = {}
            history = pd.DataFrame()

            try:
                fast_info = ticker.fast_info
            except Exception as exc:
                logger.debug(
                    "NIFTY fast_info failed: {}",
                    exc,
                )

            try:
                info = ticker.info or {}
            except Exception as exc:
                logger.debug(
                    "NIFTY ticker.info failed: {}",
                    exc,
                )

            try:
                history = ticker.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                )
            except Exception as exc:
                logger.debug(
                    "NIFTY history failed: {}",
                    exc,
                )

            return fast_info, info, history

        fast_info, info, history = await asyncio.to_thread(
            _fetch
        )

        # ----------------------------------------------------
        # Current index value
        # ----------------------------------------------------

        value_candidates: list[Any] = []

        try:
            if fast_info is not None:
                value_candidates.append(
                    fast_info.get("last_price")
                )
        except Exception:
            pass

        value_candidates.extend(
            [
                info.get("regularMarketPrice"),
                info.get("currentPrice"),
            ]
        )

        # Prefer the latest actual historical close where
        # available because it represents the latest completed
        # market session and keeps the displayed value aligned
        # with the previous-close calculation.

        historical_latest = None

        if (
            isinstance(history, pd.DataFrame)
            and not history.empty
            and "Close" in history.columns
        ):
            close_series = (
                history["Close"]
                .dropna()
            )

            if not close_series.empty:
                historical_latest = _safe_float(
                    close_series.iloc[-1]
                )

        value = (
            historical_latest
            if historical_latest is not None
            else next(
                (
                    candidate
                    for candidate in value_candidates
                    if _safe_float(candidate) is not None
                ),
                None,
            )
        )

        value = _safe_float(value)

        # ----------------------------------------------------
        # Previous close — HISTORICAL, not metadata
        # ----------------------------------------------------

        previous = None

        if (
            isinstance(history, pd.DataFrame)
            and not history.empty
            and "Close" in history.columns
        ):
            close_series = (
                history["Close"]
                .dropna()
            )

            if len(close_series) >= 2:
                previous = _safe_float(
                    close_series.iloc[-2]
                )

        # Only use metadata as a last-resort fallback.
        if previous is None:
            previous_candidates: list[Any] = []

            try:
                if fast_info is not None:
                    previous_candidates.append(
                        fast_info.get("previous_close")
                    )
            except Exception:
                pass

            previous_candidates.append(
                info.get(
                    "regularMarketPreviousClose"
                )
            )

            previous = next(
                (
                    candidate
                    for candidate in previous_candidates
                    if _safe_float(candidate) is not None
                ),
                None,
            )

            previous = _safe_float(previous)

        # ----------------------------------------------------
        # Change
        # ----------------------------------------------------

        change = None
        change_pct = None

        if (
            value is not None
            and previous is not None
            and previous != 0
        ):
            change = value - previous
            change_pct = (
                change / previous
            ) * 100

        # ----------------------------------------------------
        # Unavailable
        # ----------------------------------------------------

        if value is None:
            logger.warning(
                "NIFTY 50 index value unavailable."
            )

            return {
                "index": "NIFTY 50",
                "value": None,
                "previous_close": None,
                "change": None,
                "change_pct": None,
                "status": "unavailable",
                "source": "yfinance",
                "timestamp": _now().isoformat(),
            }

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result = {
            "index": "NIFTY 50",
            "value": _round(value),
            "previous_close": _round(previous),
            "change": _round(change),
            "change_pct": _round(change_pct),
            "status": "success",
            "source": "yfinance",
            "timestamp": _now().isoformat(),
        }

        _nifty_index_cache = {
            "data": result,
            "timestamp": _now(),
        }

        logger.info(
            "✅ NIFTY 50: value={}, previous={}, change={}, change_pct={}",
            result["value"],
            result["previous_close"],
            result["change"],
            result["change_pct"],
        )

        return result

    except Exception as exc:
        logger.exception(
            "Error fetching NIFTY 50 index: {}",
            exc,
        )

        return {
            "index": "NIFTY 50",
            "value": None,
            "previous_close": None,
            "change": None,
            "change_pct": None,
            "status": "error",
            "error": "Unable to retrieve NIFTY 50 data.",
            "source": "yfinance",
            "timestamp": _now().isoformat(),
        }


# ============================================================
# Compatibility Alias
# ============================================================

async def get_nifty50() -> dict:
    """
    Compatibility wrapper for existing frontend/router code.
    """
    return await get_nifty_index()


# ============================================================
# Cache Management
# ============================================================

def clear_market_data_cache() -> None:
    """Clear all market-data caches."""

    global _stock_cache
    global _nifty_snapshot_cache
    global _nifty_index_cache

    _stock_cache = {}

    _nifty_snapshot_cache = {
        "data": None,
        "timestamp": None,
    }

    _nifty_index_cache = {
        "data": None,
        "timestamp": None,
    }

    logger.info(
        "🗑️ Market data caches cleared."
    )