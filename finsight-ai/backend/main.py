"""
FinSight AI — FastAPI Application Entry Point
LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis

Team: Amaan Siddiqui, Achuta Rao M, Shreejal Dash, Kishan Kumar
Guide: Mrs. Anjali Vyas, Dept of CSE, DBIT Bengaluru (2025-2026)
"""

import os
import sqlite3
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Load environment variables
load_dotenv()

# ── Lifespan: startup & shutdown events ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    logger.info("🚀 FinSight AI starting up...")

    # Initialize SQLite for paper trading (dev mode)
    _init_sqlite()

    # Start background scheduler for market data refresh
    from services.scheduler import start_scheduler
    scheduler = start_scheduler()
    logger.info("⏰ Scheduler started (30-min refresh cycle)")

    yield  # app is running

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("🛑 FinSight AI shutting down.")


def _init_sqlite():
    """Create paper-trading tables if they don't exist."""
    db_path = os.getenv("SQLITE_DB_PATH", "./finsight.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT 'default',
            stock_symbol TEXT NOT NULL,
            quantity    REAL NOT NULL,
            buy_price   REAL NOT NULL,
            buy_date    TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT 'default',
            symbol      TEXT NOT NULL,
            action      TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
            quantity    REAL NOT NULL,
            price       REAL NOT NULL,
            timestamp   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT 'default',
            role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content     TEXT NOT NULL,
            timestamp   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS virtual_balance (
            user_id     TEXT PRIMARY KEY DEFAULT 'default',
            balance     REAL NOT NULL DEFAULT 100000.0,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        -- Seed default balance if not exists
        INSERT OR IGNORE INTO virtual_balance (user_id, balance)
        VALUES ('default', 100000.0);
    """)

    conn.commit()
    conn.close()
    logger.info(f"✅ SQLite initialized at {db_path}")


# ── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="FinSight AI",
    description=(
        "LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis. "
        "Powered by Gemini 1.5 Flash, ChromaDB RAG, and multi-source sentiment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ────────────────────────────────────────
from routers.chat import router as chat_router
from routers.signals import router as signals_router
from routers.ipo import router as ipo_router
from routers.sip import router as sip_router
from routers.portfolio import router as portfolio_router

app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(signals_router, prefix="/api", tags=["Signals"])
app.include_router(ipo_router, prefix="/api", tags=["IPO"])
app.include_router(sip_router, prefix="/api", tags=["SIP"])
app.include_router(portfolio_router, prefix="/api", tags=["Portfolio"])


# ── Health Check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    """Root health-check endpoint."""
    return {
        "status": "healthy",
        "service": "FinSight AI",
        "version": "1.0.0",
        "description": "LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis",
    }


@app.get("/api/health", tags=["Health"])
async def api_health():
    """API health endpoint with component status."""
    return {
        "status": "healthy",
        "components": {
            "fastapi": "running",
            "sqlite": "connected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing_key",
            "scheduler": "active",
        },
    }


# ── Run with Uvicorn ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True,
        log_level="info",
    )
