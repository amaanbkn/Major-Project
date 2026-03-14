"""
FinSight AI — Signals Router
GET /api/signal/{symbol} — Technical Buy/Hold/Sell signal for a stock.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/signal/{symbol}")
async def get_signal(symbol: str):
    """
    Get technical signal for a stock.
    Returns RSI, SMA 50/200, MA crossover, and composite Buy/Hold/Sell signal.
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid stock symbol")

    symbol = symbol.upper().strip()
    logger.info(f"📈 Signal request for {symbol}")

    from services.signals_engine import compute_signals
    result = await compute_signals(symbol)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=404,
            detail=result.get("error", f"Could not compute signals for {symbol}"),
        )

    return result


@router.get("/signal/{symbol}/recommendation")
async def get_recommendation_endpoint(symbol: str):
    """
    Get combined recommendation (technical + sentiment) for a stock.
    """
    symbol = symbol.upper().strip()
    logger.info(f"🎯 Recommendation request for {symbol}")

    from agents.recommendation_engine import get_recommendation
    result = await get_recommendation(symbol)
    return result
