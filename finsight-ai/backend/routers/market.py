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
    Return weighted market sentiment from ET RSS + Moneycontrol RSS + Reddit.
    Weights: ET 40% + MC 40% + Reddit 20%
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
