"""
FinSight AI — Market Data Router
GET /api/market/nifty50    — NIFTY 50 index + constituent stocks snapshot
GET /api/market/sentiment  — Weighted multi-source market sentiment
GET /api/stock/{symbol}    — Stock price + historical chart data
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/market/nifty50")
async def nifty50_snapshot():
    """
    Return NIFTY 50 index value + snapshot of all 50 constituent stocks.
    Response shape:
      { index: { value, change, change_pct }, stocks: [ { symbol, price, change, change_pct } ] }
    """
    logger.info("📊 NIFTY 50 snapshot requested")

    from services.market_data import get_nifty_index, get_nifty50_snapshot

    try:
        index_data = await get_nifty_index()
        stocks = await get_nifty50_snapshot()

        return {
            "index": index_data,
            "stocks": stocks,
            "count": len(stocks),
        }
    except Exception as e:
        logger.error(f"NIFTY 50 snapshot error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch NIFTY 50 data: {str(e)}")


@router.get("/market/sentiment")
async def market_sentiment():
    """
    Return weighted market sentiment from ET RSS + Moneycontrol RSS.
    Weights: ET 50% + MC 50%
    """
    logger.info("🔍 Market sentiment requested")

    from services.sentiment import get_market_sentiment

    try:
        sentiment = await get_market_sentiment()
        return sentiment
    except Exception as e:
        logger.error(f"Sentiment fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sentiment: {str(e)}")


@router.get("/stock/{symbol}")
async def stock_data(symbol: str, period: str = "6mo"):
    """
    Return current price + historical chart data for a stock.
    Query param 'period': 1mo, 3mo, 6mo, 1y, 2y (default 6mo)
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid stock symbol")

    symbol = symbol.upper().strip()
    logger.info(f"📈 Stock data requested for {symbol} (period={period})")

    from services.market_data import get_stock_price, get_stock_history

    try:
        price_data = await get_stock_price(symbol)
        history = await get_stock_history(symbol, period=period)

        return {
            "symbol": symbol,
            "price": price_data,
            "history": history,
        }
    except Exception as e:
        logger.error(f"Stock data error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for {symbol}: {str(e)}")


@router.get("/market/nifty50/history")
async def nifty50_history(period: str = "1d"):
    """
    Return historical chart data for NIFTY 50 index (^NSEI).
    Query param 'period': 1d, 7d, 1mo, 1y, all (maps to yfinance periods)
    """
    from services.market_data import get_stock_history
    try:
        db_period = "1d"
        interval = "5m"
        p = period.lower()
        if p == "1d":
            db_period = "1d"
            interval = "5m"
        elif p == "7d":
            db_period = "5d"
            interval = "15m"
        elif p == "1m":
            db_period = "1mo"
            interval = "1d"
        elif p == "1y":
            db_period = "1y"
            interval = "1d"
        elif p == "all":
            db_period = "max"
            interval = "1mo"
        else:
            db_period = period
            interval = "1d"

        history = await get_stock_history("^NSEI", period=db_period, interval=interval)
        
        formatted = []
        for item in history:
            dt_str = item["date"]
            try:
                from datetime import datetime
                if "T" in dt_str:
                    # Strip timezone offset if python can't parse it easily
                    clean_dt_str = dt_str.split("+")[0].split("-")[0] if dt_str.count("-") > 2 else dt_str
                    # Better to let fromisoformat parse it, but if offset contains colons it works in python 3.7+
                    dt = datetime.fromisoformat(dt_str)
                else:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                
                if p in ["1d", "7d"]:
                    label = dt.strftime("%H:%M")
                else:
                    label = dt.strftime("%b %d")
            except Exception:
                label = dt_str
                
            formatted.append({
                "time": label,
                "value": item["close"],
            })
        return formatted
    except Exception as e:
        logger.error(f"NIFTY 50 history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch NIFTY 50 history: {str(e)}")
