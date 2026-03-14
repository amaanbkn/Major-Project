"""
FinSight AI — Background Scheduler
APScheduler: refreshes market data, sentiment, and IPO GMP every 30 minutes.
"""

import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger


def start_scheduler() -> AsyncIOScheduler:
    """
    Start the APScheduler with 30-min refresh jobs.
    Jobs:
      1. Refresh NIFTY 50 snapshot
      2. Re-score sentiment from RSS feeds
      3. Update IPO GMP prices
    """
    interval = int(os.getenv("SCHEDULER_INTERVAL_MIN", 30))
    scheduler = AsyncIOScheduler()

    # Job 1: Refresh NIFTY 50 market snapshot
    scheduler.add_job(
        _refresh_market_data,
        "interval",
        minutes=interval,
        id="refresh_market_data",
        name="Refresh NIFTY 50 Market Data",
        replace_existing=True,
    )

    # Job 2: Re-score sentiment
    scheduler.add_job(
        _refresh_sentiment,
        "interval",
        minutes=interval,
        id="refresh_sentiment",
        name="Refresh Market Sentiment",
        replace_existing=True,
    )

    # Job 3: Update IPO GMP
    scheduler.add_job(
        _refresh_ipo_data,
        "interval",
        minutes=interval,
        id="refresh_ipo_data",
        name="Refresh IPO/GMP Data",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"⏰ Scheduler started: {interval}-min refresh cycle for market, sentiment, IPO")
    return scheduler


async def _refresh_market_data():
    """Refresh NIFTY 50 snapshot."""
    try:
        from services.market_data import get_nifty50_snapshot
        await get_nifty50_snapshot()
        logger.info("📊 Market data refreshed successfully")
    except Exception as e:
        logger.error(f"Market data refresh failed: {e}")


async def _refresh_sentiment():
    """Refresh sentiment scores from all sources."""
    try:
        from services.sentiment import clear_sentiment_cache, get_market_sentiment
        clear_sentiment_cache()
        await get_market_sentiment()
        logger.info("📰 Sentiment refreshed successfully")
    except Exception as e:
        logger.error(f"Sentiment refresh failed: {e}")


async def _refresh_ipo_data():
    """Refresh IPO and GMP data."""
    try:
        from services.ipo_tracker import clear_ipo_cache, get_upcoming_ipos
        clear_ipo_cache()
        await get_upcoming_ipos()
        logger.info("📋 IPO data refreshed successfully")
    except Exception as e:
        logger.error(f"IPO data refresh failed: {e}")
