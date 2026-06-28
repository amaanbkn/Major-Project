import pytest
import sqlite3
import os
import asyncio
from unittest.mock import patch, MagicMock

# Set up test database before importing module
TEST_DB_PATH = "./test_finsight.db"
os.environ["SQLITE_DB_PATH"] = TEST_DB_PATH

from trading_engine import buy_stock, sell_stock, get_portfolio, reset_portfolio

@pytest.fixture(autouse=True)
def setup_db():
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            stock_symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            buy_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            timestamp TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS virtual_balance (
            user_id TEXT PRIMARY KEY DEFAULT 'default',
            balance REAL NOT NULL DEFAULT 100000.0,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    
    # Run test
    yield
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.mark.asyncio
async def test_buy_stock_success():
    result = await buy_stock("test_user", "TCS", 10, 3500.0)
    assert result["status"] == "success"
    assert "Successfully bought 10 shares of TCS" in result["message"]

@pytest.mark.asyncio
async def test_buy_stock_insufficient_funds():
    result = await buy_stock("test_user", "TCS", 1000, 3500.0)
    assert result["status"] == "error"
    assert "Insufficient balance" in result["message"]

@pytest.mark.asyncio
async def test_sell_stock_success():
    await buy_stock("test_user", "INFY", 50, 1500.0)
    result = await sell_stock("test_user", "INFY", 20, 1600.0)
    assert result["status"] == "success"
    assert "Successfully sold 20 shares of INFY" in result["message"]

@pytest.mark.asyncio
async def test_sell_stock_not_enough_shares():
    await buy_stock("test_user", "HDFC", 10, 1600.0)
    result = await sell_stock("test_user", "HDFC", 20, 1600.0)
    assert result["status"] == "error"
    assert "Insufficient quantity" in result["message"]

@pytest.mark.asyncio
async def test_get_portfolio():
    await buy_stock("test_user", "ITC", 100, 400.0)
    portfolio = await get_portfolio("test_user")
    assert portfolio["balance"] == 100000.0 - (100 * 400.0)
    assert len(portfolio["holdings"]) == 1
    assert portfolio["holdings"][0]["symbol"] == "ITC"
    assert portfolio["holdings"][0]["quantity"] == 100

@pytest.mark.asyncio
async def test_reset_portfolio():
    await buy_stock("test_user", "ITC", 100, 400.0)
    await reset_portfolio("test_user")
    portfolio = await get_portfolio("test_user")
    assert portfolio["balance"] == 100000.0
    assert len(portfolio["holdings"]) == 0
