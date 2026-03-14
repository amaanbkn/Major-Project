"""
FinSight AI — Market Data Service
Fetches live stock data via yfinance and NSE data via nsepython.
Provides: LTP, OHLC, NIFTY 50 snapshot, company info, historical data.
"""

import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger

# ── In-memory cache ─────────────────────────────────────────
_nifty50_cache: dict = {"data": None, "timestamp": None}
CACHE_TTL = timedelta(minutes=15)


# ── NIFTY 50 Constituents ───────────────────────────────────
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BAJFINANCE", "BHARTIARTL",
    "KOTAKBANK", "LT", "HCLTECH", "AXISBANK", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "BAJAJFINSV",
    "WIPRO", "NESTLEIND", "NTPC", "TECHM", "POWERGRID",
    "TATAMOTORS", "M&M", "JSWSTEEL", "ADANIENT", "ADANIPORTS",
    "TATASTEEL", "ONGC", "HDFCLIFE", "DIVISLAB", "SBILIFE",
    "BAJAJ-AUTO", "GRASIM", "CIPLA", "APOLLOHOSP", "DRREDDY",
    "COALINDIA", "BPCL", "BRITANNIA", "EICHERMOT", "TATACONSUM",
    "HEROMOTOCO", "INDUSINDBK", "UPL", "BEL", "TRENT",
]


def _nse_symbol(symbol: str) -> str:
    """Convert plain symbol to NSE Yahoo Finance ticker."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    return symbol


async def get_stock_price(symbol: str) -> dict:
    """
    Fetch current/latest stock price data for a given symbol.
    Returns: symbol, price, change, change_pct, volume, timestamp.
    """
    try:
        ticker = yf.Ticker(_nse_symbol(symbol))
        info = await asyncio.to_thread(lambda: ticker.info)

        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
        change = round(price - prev_close, 2) if price and prev_close else 0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0

        return {
            "symbol": symbol.upper().replace(".NS", ""),
            "price": price,
            "previous_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "volume": info.get("volume", 0),
            "day_high": info.get("dayHigh", 0),
            "day_low": info.get("dayLow", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "price": 0,
            "status": "error",
            "error": str(e),
        }


async def get_stock_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> list[dict]:
    """
    Fetch historical OHLCV data for charting.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    """
    try:
        ticker = yf.Ticker(_nse_symbol(symbol))
        df: pd.DataFrame = await asyncio.to_thread(
            lambda: ticker.history(period=period, interval=interval)
        )

        if df.empty:
            return []

        df = df.reset_index()
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": row["Date"].isoformat() if hasattr(row["Date"], "isoformat") else str(row["Date"]),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
        return records
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return []


async def get_company_info(symbol: str) -> dict:
    """Fetch company metadata: sector, industry, description."""
    try:
        ticker = yf.Ticker(_nse_symbol(symbol))
        info = await asyncio.to_thread(lambda: ticker.info)
        return {
            "symbol": symbol.upper(),
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", ""),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees", 0),
        }
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {e}")
        return {"symbol": symbol.upper(), "status": "error", "error": str(e)}


async def get_nifty50_snapshot() -> list[dict]:
    """
    Get a snapshot of all NIFTY 50 stocks: symbol, price, change%.
    Uses 15-min cache to avoid excessive API calls.
    """
    global _nifty50_cache

    # Check cache
    if (
        _nifty50_cache["data"]
        and _nifty50_cache["timestamp"]
        and (datetime.now() - _nifty50_cache["timestamp"]) < CACHE_TTL
    ):
        logger.debug("Returning cached NIFTY 50 snapshot")
        return _nifty50_cache["data"]

    logger.info("Refreshing NIFTY 50 snapshot...")
    snapshot = []

    # Batch fetch using yfinance download (much faster than individual calls)
    try:
        tickers_str = " ".join([_nse_symbol(s) for s in NIFTY_50_SYMBOLS])
        df = await asyncio.to_thread(
            lambda: yf.download(tickers_str, period="2d", group_by="ticker", progress=False)
        )

        for sym in NIFTY_50_SYMBOLS:
            try:
                nse_sym = _nse_symbol(sym)
                if nse_sym in df.columns.get_level_values(0):
                    ticker_data = df[nse_sym]
                    if len(ticker_data) >= 2:
                        latest = ticker_data.iloc[-1]
                        prev = ticker_data.iloc[-2]
                        price = round(float(latest["Close"]), 2)
                        prev_close = round(float(prev["Close"]), 2)
                        change = round(price - prev_close, 2)
                        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
                    else:
                        latest = ticker_data.iloc[-1]
                        price = round(float(latest["Close"]), 2)
                        change = 0
                        change_pct = 0

                    snapshot.append({
                        "symbol": sym,
                        "price": price,
                        "change": change,
                        "change_pct": change_pct,
                    })
            except Exception as e:
                logger.warning(f"Skipping {sym} in NIFTY50 snapshot: {e}")
                continue

    except Exception as e:
        logger.error(f"NIFTY 50 batch download failed: {e}")
        # Fallback: return empty but don't crash
        return []

    _nifty50_cache = {"data": snapshot, "timestamp": datetime.now()}
    logger.info(f"✅ NIFTY 50 snapshot refreshed: {len(snapshot)} stocks")
    return snapshot


async def get_nifty_index() -> dict:
    """Get NIFTY 50 index value."""
    try:
        ticker = yf.Ticker("^NSEI")
        info = await asyncio.to_thread(lambda: ticker.info)
        price = info.get("regularMarketPrice", 0)
        prev = info.get("regularMarketPreviousClose", 0)
        change = round(price - prev, 2) if price and prev else 0
        change_pct = round((change / prev) * 100, 2) if prev else 0

        return {
            "index": "NIFTY 50",
            "value": price,
            "change": change,
            "change_pct": change_pct,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching NIFTY index: {e}")
        return {"index": "NIFTY 50", "value": 0, "status": "error"}
