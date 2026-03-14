"""
FinSight AI — Sentiment Analysis Service
Weighted multi-source sentiment: ET RSS (40%) + Moneycontrol RSS (40%) + Reddit PRAW (20%)
Reddit filter: r/IndiaInvestments, upvote_ratio > 0.85, top 5 posts only
"""

import asyncio
import os
import re
from datetime import datetime, timedelta
from typing import Optional

import feedparser
from loguru import logger

# ── In-memory cache ─────────────────────────────────────────
_sentiment_cache: dict = {}
CACHE_TTL = timedelta(seconds=int(os.getenv("RSS_CACHE_TTL", 900)))

# ── RSS Feed URLs ────────────────────────────────────────────
RSS_FEEDS = {
    "economic_times": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    ],
    "moneycontrol": [
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://www.moneycontrol.com/rss/stocksnews.xml",
    ],
}

# ── Sentiment keyword dictionaries ──────────────────────────
POSITIVE_WORDS = {
    "surge", "rally", "gain", "bull", "bullish", "rise", "soar", "jump",
    "high", "record", "profit", "growth", "upbeat", "optimistic", "strong",
    "outperform", "buy", "upgrade", "recovery", "boom", "positive",
    "momentum", "breakout", "beat", "up", "advances", "climbs", "surges",
    "accumulate", "attractive", "undervalued", "robust", "dividend",
}

NEGATIVE_WORDS = {
    "crash", "fall", "bear", "bearish", "decline", "drop", "plunge",
    "low", "loss", "slump", "weak", "pessimistic", "sell", "downgrade",
    "recession", "panic", "volatile", "fear", "correction", "tank",
    "negative", "breakdown", "risk", "down", "tumbles", "slips", "sinks",
    "overvalued", "expensive", "debt", "default", "fraud", "scam",
}


def _analyze_text_sentiment(text: str) -> float:
    """
    Simple keyword-based sentiment score.
    Returns a score between -1.0 (very negative) and 1.0 (very positive).
    """
    if not text:
        return 0.0

    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)
    total = pos_count + neg_count

    if total == 0:
        return 0.0

    return round((pos_count - neg_count) / total, 3)


async def _fetch_rss_sentiment(source_name: str, urls: list[str]) -> dict:
    """Fetch and analyze sentiment from RSS feeds."""
    articles = []
    scores = []

    for url in urls:
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries[:10]:  # Top 10 articles per feed
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined_text = f"{title} {summary}"
                score = _analyze_text_sentiment(combined_text)
                scores.append(score)
                articles.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "sentiment_score": score,
                    "source": source_name,
                })
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source_name} ({url}): {e}")
            continue

    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0

    return {
        "source": source_name,
        "avg_score": avg_score,
        "article_count": len(articles),
        "articles": articles[:5],  # Return top 5 for display
    }


async def _fetch_reddit_sentiment() -> dict:
    """
    Fetch sentiment from r/IndiaInvestments via PRAW.
    Filter: upvote_ratio > 0.85, top 5 posts only.
    """
    try:
        import praw

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "FinSightAI/1.0"),
        )

        subreddit = reddit.subreddit("IndiaInvestments")
        posts = []
        scores = []

        hot_posts = await asyncio.to_thread(
            lambda: list(subreddit.hot(limit=20))
        )

        for post in hot_posts:
            if post.upvote_ratio > 0.85 and not post.stickied:
                combined_text = f"{post.title} {post.selftext[:500]}"
                score = _analyze_text_sentiment(combined_text)
                scores.append(score)
                posts.append({
                    "title": post.title,
                    "link": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "sentiment_score": score,
                    "source": "reddit",
                })
                if len(posts) >= 5:
                    break

        avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0

        return {
            "source": "reddit_india_investments",
            "avg_score": avg_score,
            "post_count": len(posts),
            "posts": posts,
        }

    except ImportError:
        logger.warning("PRAW not installed. Skipping Reddit sentiment.")
        return {"source": "reddit_india_investments", "avg_score": 0.0, "post_count": 0, "posts": []}
    except Exception as e:
        logger.error(f"Reddit sentiment fetch failed: {e}")
        return {"source": "reddit_india_investments", "avg_score": 0.0, "post_count": 0, "posts": [], "error": str(e)}


async def get_market_sentiment(symbol: Optional[str] = None) -> dict:
    """
    Get weighted market sentiment from all sources.
    Weights: Economic Times RSS (40%) + Moneycontrol RSS (40%) + Reddit (20%)
    Uses 15-min cache to avoid excessive requests.
    """
    cache_key = symbol or "market_general"

    # Check cache
    if cache_key in _sentiment_cache:
        cached = _sentiment_cache[cache_key]
        if (datetime.now() - cached["timestamp"]) < CACHE_TTL:
            logger.debug(f"Returning cached sentiment for {cache_key}")
            return cached["data"]

    logger.info(f"🔍 Fetching sentiment for: {cache_key}")

    # Fetch all sources concurrently
    et_task = _fetch_rss_sentiment("economic_times", RSS_FEEDS["economic_times"])
    mc_task = _fetch_rss_sentiment("moneycontrol", RSS_FEEDS["moneycontrol"])
    reddit_task = _fetch_reddit_sentiment()

    et_result, mc_result, reddit_result = await asyncio.gather(
        et_task, mc_task, reddit_task
    )

    # Weighted composite score
    # ET: 40%, Moneycontrol: 40%, Reddit: 20%
    weighted_score = round(
        (et_result["avg_score"] * 0.40)
        + (mc_result["avg_score"] * 0.40)
        + (reddit_result["avg_score"] * 0.20),
        3,
    )

    # Determine sentiment label
    if weighted_score > 0.2:
        label = "Bullish"
    elif weighted_score > 0.05:
        label = "Slightly Bullish"
    elif weighted_score > -0.05:
        label = "Neutral"
    elif weighted_score > -0.2:
        label = "Slightly Bearish"
    else:
        label = "Bearish"

    result = {
        "overall_score": weighted_score,
        "overall_label": label,
        "sources": {
            "economic_times": {
                "score": et_result["avg_score"],
                "weight": 0.40,
                "articles": et_result.get("articles", []),
            },
            "moneycontrol": {
                "score": mc_result["avg_score"],
                "weight": 0.40,
                "articles": mc_result.get("articles", []),
            },
            "reddit": {
                "score": reddit_result["avg_score"],
                "weight": 0.20,
                "posts": reddit_result.get("posts", []),
            },
        },
        "timestamp": datetime.now().isoformat(),
    }

    # Update cache
    _sentiment_cache[cache_key] = {"data": result, "timestamp": datetime.now()}
    logger.info(f"✅ Sentiment computed: {label} ({weighted_score})")

    return result


def clear_sentiment_cache():
    """Clear the sentiment cache (called by scheduler after refresh)."""
    global _sentiment_cache
    _sentiment_cache = {}
    logger.info("🗑️ Sentiment cache cleared")
