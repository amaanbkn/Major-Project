from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel, Field
from dependencies import get_current_user

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
async def get_portfolio(current_user: str = Depends(get_current_user)):
    """Get user's paper trading portfolio."""
    logger.info(f"💼 Portfolio request for {current_user}")
    from trading_engine import get_portfolio as _get_portfolio
    portfolio = await _get_portfolio(current_user)

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
async def buy_stock(request: TradeRequest, current_user: str = Depends(get_current_user)):
    """Execute a paper BUY order."""
    symbol = request.symbol.upper().strip()
    logger.info(f"📈 BUY request: {request.quantity}x {symbol} for {current_user}")

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
    result = await _buy_stock(current_user, symbol, request.quantity, price)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/portfolio/sell")
async def sell_stock(request: TradeRequest, current_user: str = Depends(get_current_user)):
    """Execute a paper SELL order."""
    symbol = request.symbol.upper().strip()
    logger.info(f"📉 SELL request: {request.quantity}x {symbol} for {current_user}")

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
    result = await _sell_stock(current_user, symbol, request.quantity, price)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/portfolio/transactions")
async def get_transactions(limit: int = 50, current_user: str = Depends(get_current_user)):
    """Get transaction history."""
    from trading_engine import get_transaction_history
    transactions = await get_transaction_history(current_user, limit)
    return {"transactions": transactions, "count": len(transactions)}


@router.post("/portfolio/reset")
async def reset_portfolio(request: ResetRequest, current_user: str = Depends(get_current_user)):
    """Reset portfolio to initial ₹1,00,000 balance."""
    from trading_engine import reset_portfolio as _reset_portfolio
    result = await _reset_portfolio(current_user)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result



