"""
FinSight AI — FastAPI Application Entry Point
LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis

Team: Amaan Siddiqui, Achuta Rao M, Shreejal Dash, Kishan Kumar
"""

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env", override=True)

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
    if not Path(db_path).is_absolute():
        db_path = str(BACKEND_DIR / db_path)
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

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id     TEXT PRIMARY KEY DEFAULT 'default',
            display_name TEXT DEFAULT 'Amaan Siddiqui',
            updated_at  TEXT DEFAULT (datetime('now'))
        );
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
frontend_url = (os.getenv("FRONTEND_URL", "http://localhost:5174") or "").rstrip("/")
environment = os.getenv("ENVIRONMENT", "development").lower()

allowed_origins = {
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
}
if frontend_url:
    allowed_origins.add(frontend_url)

if environment == "production":
    allowed_origins = {origin for origin in allowed_origins if origin}
    if frontend_url:
        allowed_origins.add(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
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
from routers.market import router as market_router
from routers.user import router as user_router
from routers.rag import router as rag_router

app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(signals_router, prefix="/api", tags=["Signals"])
app.include_router(ipo_router, prefix="/api", tags=["IPO"])
app.include_router(sip_router, prefix="/api", tags=["SIP"])
app.include_router(portfolio_router, prefix="/api", tags=["Portfolio"])
app.include_router(market_router, prefix="/api", tags=["Market"])
app.include_router(user_router, prefix="/api", tags=["User"])
app.include_router(rag_router, prefix="/api", tags=["RAG"])


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
    gemini_status = "missing_key"
    try:
        from services.gemini import get_gemini_status
        status = get_gemini_status()
        gemini_status = "configured" if status.get("configured") else "missing_key"
    except Exception:
        gemini_status = "error"

    return {
        "status": "healthy",
        "components": {
            "fastapi": "running",
            "sqlite": "connected",
            "gemini": gemini_status,
            "scheduler": "active",
        },
    }


# ── Run with Uvicorn ─────────────────────────────────────────
if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True,
        log_level="info",
    )
