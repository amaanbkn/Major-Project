"""
FinSight AI — Paper Trading Engine
Virtual paper trading with ₹1,00,000 starting balance.
SQLite-backed: portfolio management, P&L, transaction history.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

from loguru import logger

# ── Singleton SQLite connection ──────────────────────────────
_db_path = os.getenv("SQLITE_DB_PATH", "./finsight.db")


def _get_conn() -> sqlite3.Connection:
    """Get SQLite connection (Singleton pattern via check_same_thread)."""
    conn = sqlite3.connect(_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


async def get_portfolio(user_id: str = "default") -> dict:
    """
    Get complete portfolio for a user:
    - Virtual balance
    - All holdings with current P&L
    - Total portfolio value
    """
    conn = _get_conn()
    try:
        # Get balance
        row = conn.execute(
            "SELECT balance FROM virtual_balance WHERE user_id = ?", (user_id,)
        ).fetchone()
        balance = row["balance"] if row else 100000.0

        # Get holdings
        holdings_rows = conn.execute(
            "SELECT stock_symbol, quantity, buy_price, buy_date FROM portfolios WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        holdings = []
        total_invested = 0
        total_current = 0

        for h in holdings_rows:
            invested = h["quantity"] * h["buy_price"]
            total_invested += invested
            holdings.append({
                "symbol": h["stock_symbol"],
                "quantity": h["quantity"],
                "buy_price": h["buy_price"],
                "buy_date": h["buy_date"],
                "invested_value": round(invested, 2),
                "current_price": None,  # Will be filled by caller if needed
            })

        return {
            "user_id": user_id,
            "balance": round(balance, 2),
            "holdings": holdings,
            "total_invested": round(total_invested, 2),
            "portfolio_value": round(balance + total_invested, 2),
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        conn.close()


async def buy_stock(
    user_id: str,
    symbol: str,
    quantity: float,
    price: float,
) -> dict:
    """
    Execute a paper BUY order.
    Deducts from virtual balance, adds to portfolio.
    """
    conn = _get_conn()
    try:
        total_cost = quantity * price

        # Check balance
        row = conn.execute(
            "SELECT balance FROM virtual_balance WHERE user_id = ?", (user_id,)
        ).fetchone()
        balance = row["balance"] if row else 100000.0

        if total_cost > balance:
            return {
                "status": "error",
                "message": f"Insufficient balance. Available: ₹{balance:,.2f}, Required: ₹{total_cost:,.2f}",
            }

        # Deduct balance
        new_balance = balance - total_cost
        conn.execute(
            "UPDATE virtual_balance SET balance = ?, updated_at = datetime('now') WHERE user_id = ?",
            (new_balance, user_id),
        )

        # Check if already holding this stock
        existing = conn.execute(
            "SELECT id, quantity, buy_price FROM portfolios WHERE user_id = ? AND stock_symbol = ?",
            (user_id, symbol.upper()),
        ).fetchone()

        if existing:
            # Average out the buy price
            new_qty = existing["quantity"] + quantity
            avg_price = (
                (existing["quantity"] * existing["buy_price"]) + (quantity * price)
            ) / new_qty
            conn.execute(
                "UPDATE portfolios SET quantity = ?, buy_price = ? WHERE id = ?",
                (new_qty, round(avg_price, 2), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO portfolios (user_id, stock_symbol, quantity, buy_price, buy_date) VALUES (?, ?, ?, ?, ?)",
                (user_id, symbol.upper(), quantity, price, datetime.now().strftime("%Y-%m-%d")),
            )

        # Record transaction
        conn.execute(
            "INSERT INTO transactions (user_id, symbol, action, quantity, price) VALUES (?, ?, 'BUY', ?, ?)",
            (user_id, symbol.upper(), quantity, price),
        )

        conn.commit()

        logger.info(f"📈 BUY executed: {quantity}x {symbol} @ ₹{price} for user {user_id}")

        return {
            "status": "success",
            "action": "BUY",
            "symbol": symbol.upper(),
            "quantity": quantity,
            "price": price,
            "total_cost": round(total_cost, 2),
            "remaining_balance": round(new_balance, 2),
            "message": f"Successfully bought {quantity} shares of {symbol.upper()} at ₹{price:,.2f}",
        }
    except Exception as e:
        logger.error(f"Buy error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


async def sell_stock(
    user_id: str,
    symbol: str,
    quantity: float,
    price: float,
) -> dict:
    """
    Execute a paper SELL order.
    Removes from portfolio, adds to virtual balance.
    """
    conn = _get_conn()
    try:
        # Check holdings
        existing = conn.execute(
            "SELECT id, quantity, buy_price FROM portfolios WHERE user_id = ? AND stock_symbol = ?",
            (user_id, symbol.upper()),
        ).fetchone()

        if not existing:
            return {
                "status": "error",
                "message": f"No holdings found for {symbol.upper()}",
            }

        if quantity > existing["quantity"]:
            return {
                "status": "error",
                "message": f"Insufficient quantity. Holding: {existing['quantity']}, Requested: {quantity}",
            }

        total_value = quantity * price
        pnl = (price - existing["buy_price"]) * quantity
        pnl_pct = ((price - existing["buy_price"]) / existing["buy_price"]) * 100

        # Update balance
        row = conn.execute(
            "SELECT balance FROM virtual_balance WHERE user_id = ?", (user_id,)
        ).fetchone()
        balance = row["balance"] if row else 100000.0
        new_balance = balance + total_value
        conn.execute(
            "UPDATE virtual_balance SET balance = ?, updated_at = datetime('now') WHERE user_id = ?",
            (new_balance, user_id),
        )

        # Update or remove holding
        new_qty = existing["quantity"] - quantity
        if new_qty <= 0:
            conn.execute("DELETE FROM portfolios WHERE id = ?", (existing["id"],))
        else:
            conn.execute(
                "UPDATE portfolios SET quantity = ? WHERE id = ?",
                (new_qty, existing["id"]),
            )

        # Record transaction
        conn.execute(
            "INSERT INTO transactions (user_id, symbol, action, quantity, price) VALUES (?, ?, 'SELL', ?, ?)",
            (user_id, symbol.upper(), quantity, price),
        )

        conn.commit()

        logger.info(f"📉 SELL executed: {quantity}x {symbol} @ ₹{price} | P&L: ₹{pnl:,.2f}")

        return {
            "status": "success",
            "action": "SELL",
            "symbol": symbol.upper(),
            "quantity": quantity,
            "price": price,
            "total_value": round(total_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "remaining_balance": round(new_balance, 2),
            "message": f"Successfully sold {quantity} shares of {symbol.upper()} at ₹{price:,.2f}. P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)",
        }
    except Exception as e:
        logger.error(f"Sell error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


async def get_transaction_history(
    user_id: str = "default",
    limit: int = 50,
) -> list[dict]:
    """Get transaction history for a user."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT symbol, action, quantity, price, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

        return [
            {
                "symbol": r["symbol"],
                "action": r["action"],
                "quantity": r["quantity"],
                "price": r["price"],
                "total": round(r["quantity"] * r["price"], 2),
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]
    finally:
        conn.close()


async def reset_portfolio(user_id: str = "default") -> dict:
    """Reset portfolio to initial state: ₹1,00,000 balance, no holdings."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM portfolios WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE virtual_balance SET balance = 100000.0, updated_at = datetime('now') WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        logger.info(f"🔄 Portfolio reset for user {user_id}")
        return {"status": "success", "message": "Portfolio reset to ₹1,00,000"}
    except Exception as e:
        logger.error(f"Portfolio reset error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()
