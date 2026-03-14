"""
FinSight AI — Portfolio Router
CRUD /api/portfolio — Paper trading portfolio management.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

router = APIRouter()


class TradeRequest(BaseModel):
    """Paper trade request."""
    symbol: str
    quantity: float = Field(..., gt=0)
    user_id: str = "default"


class ResetRequest(BaseModel):
    """Portfolio reset request."""
    user_id: str = "default"


@router.get("/portfolio")
async def get_portfolio(user_id: str = "default"):
    """Get user's paper trading portfolio."""
    logger.info(f"💼 Portfolio request for {user_id}")
    from trading_engine import get_portfolio as _get_portfolio
    portfolio = await _get_portfolio(user_id)

    # Enrich with current prices
    from services.market_data import get_stock_price
    for holding in portfolio.get("holdings", []):
        try:
            price_data = await get_stock_price(holding["symbol"])
            holding["current_price"] = price_data.get("price", 0)
            holding["current_value"] = round(holding["quantity"] * holding["current_price"], 2)
            holding["pnl"] = round(holding["current_value"] - holding["invested_value"], 2)
            holding["pnl_pct"] = round(
                ((holding["current_price"] - holding["buy_price"]) / holding["buy_price"]) * 100, 2
            ) if holding["buy_price"] > 0 else 0
        except Exception:
            holding["current_price"] = None
            holding["current_value"] = None
            holding["pnl"] = None
            holding["pnl_pct"] = None

    return portfolio


@router.post("/portfolio/buy")
async def buy_stock(request: TradeRequest):
    """Execute a paper BUY order."""
    symbol = request.symbol.upper().strip()
    logger.info(f"📈 BUY request: {request.quantity}x {symbol} for {request.user_id}")

    # Get current price
    from services.market_data import get_stock_price
    price_data = await get_stock_price(symbol)
    price = price_data.get("price", 0)

    if not price or price <= 0:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for {symbol}. Please check the symbol.",
        )

    from trading_engine import buy_stock as _buy_stock
    result = await _buy_stock(request.user_id, symbol, request.quantity, price)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/portfolio/sell")
async def sell_stock(request: TradeRequest):
    """Execute a paper SELL order."""
    symbol = request.symbol.upper().strip()
    logger.info(f"📉 SELL request: {request.quantity}x {symbol} for {request.user_id}")

    # Get current price
    from services.market_data import get_stock_price
    price_data = await get_stock_price(symbol)
    price = price_data.get("price", 0)

    if not price or price <= 0:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for {symbol}. Please check the symbol.",
        )

    from trading_engine import sell_stock as _sell_stock
    result = await _sell_stock(request.user_id, symbol, request.quantity, price)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/portfolio/transactions")
async def get_transactions(user_id: str = "default", limit: int = 50):
    """Get transaction history."""
    from trading_engine import get_transaction_history
    transactions = await get_transaction_history(user_id, limit)
    return {"transactions": transactions, "count": len(transactions)}


@router.post("/portfolio/reset")
async def reset_portfolio(request: ResetRequest):
    """Reset portfolio to initial ₹1,00,000 balance."""
    from trading_engine import reset_portfolio as _reset_portfolio
    result = await _reset_portfolio(request.user_id)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


@router.get("/stock/{symbol}")
async def get_stock_data(symbol: str, period: str = "6mo"):
    """Get stock price + history data for charts."""
    symbol = symbol.upper().strip()
    from services.market_data import get_stock_price, get_stock_history, get_company_info

    price = await get_stock_price(symbol)
    history = await get_stock_history(symbol, period=period)
    info = await get_company_info(symbol)

    return {
        "price": price,
        "history": history,
        "info": info,
    }


@router.get("/market/nifty50")
async def get_nifty50():
    """Get NIFTY 50 snapshot."""
    from services.market_data import get_nifty50_snapshot, get_nifty_index
    snapshot = await get_nifty50_snapshot()
    index = await get_nifty_index()
    return {"index": index, "stocks": snapshot}


@router.get("/market/sentiment")
async def get_sentiment():
    """Get current market sentiment."""
    from services.sentiment import get_market_sentiment
    sentiment = await get_market_sentiment()
    return sentiment
