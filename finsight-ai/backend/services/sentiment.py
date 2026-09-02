"""
FinSight AI — Sentiment Analysis Service

Aggregates sentiment from:
    - Economic Times RSS: 50%
    - Moneycontrol RSS: 50%

Reddit is intentionally NOT used.

The service:
- Fetches multiple financial RSS feeds asynchronously
- Performs lightweight keyword-based sentiment scoring
- Filters irrelevant financial content
- Decodes HTML entities
- Sorts news by publication time
- Caches results for 15 minutes
- Handles source failures gracefully

NOTE:
The keyword scorer is a baseline heuristic and should not be
treated as a production-grade financial NLP model.
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional
from zoneinfo import ZoneInfo

import feedparser
import requests
from loguru import logger


# ============================================================
# Configuration
# ============================================================

IST = ZoneInfo("Asia/Kolkata")

CACHE_TTL = timedelta(
    seconds=int(
        os.getenv(
            "RSS_CACHE_TTL",
            "900",
        )
    )
)


# ============================================================
# RSS Feeds
# ============================================================

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


# ============================================================
# Sentiment Dictionaries
# ============================================================

POSITIVE_WORDS = {
    "surge",
    "rally",
    "gain",
    "bull",
    "bullish",
    "rise",
    "soar",
    "jump",
    "record",
    "profit",
    "growth",
    "upbeat",
    "optimistic",
    "strong",
    "outperform",
    "buy",
    "upgrade",
    "recovery",
    "boom",
    "positive",
    "momentum",
    "breakout",
    "beat",
    "up",
    "advances",
    "climbs",
    "surges",
    "accumulate",
    "attractive",
    "undervalued",
    "robust",
    "dividend",
    "improves",
    "improved",
    "improvement",
}

NEGATIVE_WORDS = {
    "crash",
    "fall",
    "bear",
    "bearish",
    "decline",
    "drop",
    "plunge",
    "loss",
    "slump",
    "weak",
    "pessimistic",
    "sell",
    "downgrade",
    "recession",
    "panic",
    "volatile",
    "fear",
    "correction",
    "tank",
    "negative",
    "breakdown",
    "risk",
    "down",
    "tumbles",
    "slips",
    "sinks",
    "overvalued",
    "expensive",
    "debt",
    "default",
    "fraud",
    "scam",
    "weakens",
    "warning",
}


# ============================================================
# News Filtering
# ============================================================

MARKET_KEYWORDS = {
    "stock",
    "stocks",
    "share",
    "shares",
    "nifty",
    "sensex",
    "market",
    "markets",
    "equity",
    "equities",
    "ipo",
    "earnings",
    "profit",
    "results",
    "investor",
    "investors",
    "sebi",
    "rbi",
    "bank",
    "banks",
    "mutual fund",
    "fund",
    "index",
    "indices",
    "trading",
    "trade",
    "valuation",
    "dividend",
    "quarter",
    "revenue",
    "futures",
    "options",
}

EXCLUDED_PHRASES = {
    "quote of the day",
    "thought of the day",
    "horoscope",
    "lifestyle",
    "entertainment",
    "recipe",
    "travel",
    "sports",
}


# ============================================================
# Cache
# ============================================================

_sentiment_cache: dict[str, dict] = {}


# ============================================================
# Helpers
# ============================================================

def _now() -> datetime:
    """Return current India Standard Time."""
    return datetime.now(IST)


def _clean_text(text: str | None) -> str:
    """Clean and decode scraped RSS text."""
    if not text:
        return ""

    text = unescape(str(text))

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _extract_published_datetime(
    entry: dict,
) -> Optional[datetime]:
    """
    Extract the publication time from a feed entry.

    Returns timezone-aware datetime in IST where possible.
    """

    # Prefer parsed RSS timestamp.
    parsed_time = entry.get(
        "published_parsed"
    ) or entry.get(
        "updated_parsed"
    )

    if parsed_time:
        try:
            dt = datetime(
                *parsed_time[:6],
                tzinfo=ZoneInfo("UTC"),
            )

            return dt.astimezone(IST)

        except Exception:
            pass

    # Try raw published/updated field.
    raw = (
        entry.get("published")
        or entry.get("updated")
        or ""
    )

    raw = _clean_text(raw)

    if raw:

        try:
            dt = parsedate_to_datetime(raw)

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=IST
                )

            return dt.astimezone(IST)

        except Exception:
            pass

    return None


def _is_relevant_market_article(
    title: str,
    summary: str,
) -> bool:
    """Determine whether a feed item is relevant to market analysis."""

    text = f"{title} {summary}".lower()

    if any(
        phrase in text
        for phrase in EXCLUDED_PHRASES
    ):
        return False

    return any(
        keyword in text
        for keyword in MARKET_KEYWORDS
    )


def _analyze_text_sentiment(
    text: str,
) -> float:
    """
    Keyword-based baseline sentiment score.

    Returns:
        -1.0 = negative
         0.0 = neutral
        +1.0 = positive
    """

    if not text:
        return 0.0

    words = set(
        re.findall(
            r"\b[a-zA-Z]+\b",
            text.lower(),
        )
    )

    positive_count = len(
        words & POSITIVE_WORDS
    )

    negative_count = len(
        words & NEGATIVE_WORDS
    )

    total = (
        positive_count
        + negative_count
    )

    if total == 0:
        return 0.0

    score = (
        positive_count
        - negative_count
    ) / total

    return round(
        max(
            -1.0,
            min(
                1.0,
                score,
            ),
        ),
        3,
    )


# ============================================================
# RSS Fetcher
# ============================================================

async def _fetch_rss_sentiment(
    source_name: str,
    urls: list[str],
    symbol: Optional[str] = None,
) -> dict:
    """
    Fetch and analyze RSS feeds for a source.
    """

    articles: list[dict] = []
    scores: list[float] = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36 "
            "FinSightAI/1.0"
        ),
        "Accept": (
            "application/rss+xml,"
            "application/xml,text/xml,"
            "text/html;q=0.9,*/*;q=0.8"
        ),
    }

    source_failures = 0

    # Normalize optional symbol.
    target_symbol = (
        symbol.upper().strip()
        if symbol
        else None
    )

    for url in urls:

        try:
            response = await asyncio.to_thread(
                requests.get,
                url,
                headers=headers,
                timeout=15,
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            if getattr(
                feed,
                "bozo",
                False,
            ):
                logger.warning(
                    f"RSS parser warning for "
                    f"{source_name}: {url}"
                )

            for entry in feed.entries:

                title = _clean_text(
                    entry.get(
                        "title",
                        "",
                    )
                )

                summary = _clean_text(
                    entry.get(
                        "summary",
                        "",
                    )
                    or entry.get(
                        "description",
                        "",
                    )
                )

                if not summary:

                    content = entry.get(
                        "content"
                    )

                    if isinstance(
                        content,
                        list,
                    ):
                        summary = _clean_text(
                            " ".join(
                                str(
                                    item.get(
                                        "value",
                                        "",
                                    )
                                )
                                for item in content
                                if isinstance(
                                    item,
                                    dict,
                                )
                            )
                        )

                if not title:
                    continue

                # ------------------------------------------------
                # General financial relevance
                # ------------------------------------------------
                if not _is_relevant_market_article(
                    title,
                    summary,
                ):
                    continue

                # ------------------------------------------------
                # Symbol filtering
                # ------------------------------------------------
                if target_symbol:

                    symbol_text = (
                        f"{title} {summary}"
                        .upper()
                    )

                    if target_symbol not in symbol_text:
                        continue

                combined_text = (
                    f"{title} {summary}".strip()
                )

                score = _analyze_text_sentiment(
                    combined_text
                )

                published_dt = (
                    _extract_published_datetime(
                        entry
                    )
                )

                published_iso = (
                    published_dt.isoformat()
                    if published_dt
                    else ""
                )

                articles.append(
                    {
                        "title": title,
                        "summary": summary[:500],
                        "link": _clean_text(
                            entry.get(
                                "link",
                                "",
                            )
                        ),
                        "published": (
                            published_dt.strftime(
                                "%Y-%m-%d %H:%M:%S %Z"
                            )
                            if published_dt
                            else ""
                        ),
                        "published_at": (
                            published_iso
                        ),
                        "sentiment_score": score,
                        "source": source_name,
                    }
                )

                scores.append(score)

        except requests.HTTPError as exc:

            source_failures += 1

            logger.warning(
                f"RSS HTTP failure for "
                f"{source_name}: "
                f"{exc}"
            )

        except requests.RequestException as exc:

            source_failures += 1

            logger.warning(
                f"RSS network failure for "
                f"{source_name}: "
                f"{exc}"
            )

        except Exception as exc:

            source_failures += 1

            logger.exception(
                f"RSS parsing failure for "
                f"{source_name}: "
                f"{exc}"
            )

    # Sort latest first.
    articles.sort(
        key=lambda article: article.get(
            "published_at",
            "",
        ),
        reverse=True,
    )

    # Remove duplicates by title.
    unique_articles: list[dict] = []
    seen_titles: set[str] = set()

    for article in articles:

        title_key = article["title"].lower()

        if title_key in seen_titles:
            continue

        seen_titles.add(title_key)
        unique_articles.append(article)

    articles = unique_articles

    avg_score = (
        round(
            sum(scores) / len(scores),
            3,
        )
        if scores
        else 0.0
    )

    return {
        "source": source_name,
        "avg_score": avg_score,
        "article_count": len(articles),
        "articles": articles[:10],
        "failed_feeds": source_failures,
        "status": (
            "ok"
            if articles
            else "unavailable"
        ),
    }


# ============================================================
# Public Sentiment API
# ============================================================

async def get_market_sentiment(
    symbol: Optional[str] = None,
) -> dict:
    """
    Get weighted market sentiment.

    Weights:
        Economic Times  = 50%
        Moneycontrol     = 50%

    The weighting is normalized to 100% because Reddit has
    been removed from the current project scope.

    A symbol can optionally be supplied for stock-specific
    news filtering.
    """

    cache_key = (
        symbol.upper().strip()
        if symbol
        else "market_general"
    )

    cached = _sentiment_cache.get(
        cache_key
    )

    if cached:

        age = (
            _now()
            - cached["timestamp"]
        )

        if age < CACHE_TTL:

            logger.debug(
                f"Returning cached sentiment "
                f"for {cache_key}"
            )

            return cached["data"]

    logger.info(
        f"🔍 Fetching sentiment for: "
        f"{cache_key}"
    )

    # Fetch ET and Moneycontrol concurrently.
    et_task = _fetch_rss_sentiment(
        "economic_times",
        RSS_FEEDS["economic_times"],
        symbol,
    )

    mc_task = _fetch_rss_sentiment(
        "moneycontrol",
        RSS_FEEDS["moneycontrol"],
        symbol,
    )

    et_result, mc_result = await asyncio.gather(
        et_task,
        mc_task,
    )

    # ========================================================
    # Weighted Score
    # ========================================================

    weighted_score = round(
        (
            et_result["avg_score"] * 0.50
        )
        + (
            mc_result["avg_score"] * 0.50
        ),
        3,
    )

    # ========================================================
    # Sentiment Label
    # ========================================================

    if weighted_score >= 0.20:
        label = "Bullish"

    elif weighted_score >= 0.05:
        label = "Slightly Bullish"

    elif weighted_score > -0.05:
        label = "Neutral"

    elif weighted_score > -0.20:
        label = "Slightly Bearish"

    else:
        label = "Bearish"

    # ========================================================
    # Result
    # ========================================================

    timestamp = _now()

    result = {
        "overall_score": weighted_score,
        "overall_label": label,

        "symbol": (
            symbol.upper()
            if symbol
            else None
        ),

        "weights": {
            "economic_times": 0.50,
            "moneycontrol": 0.50,
        },

        "sources": {
            "economic_times": {
                "score": et_result["avg_score"],
                "weight": 0.50,
                "article_count": et_result[
                    "article_count"
                ],
                "status": et_result[
                    "status"
                ],
                "articles": et_result[
                    "articles"
                ],
            },

            "moneycontrol": {
                "score": mc_result["avg_score"],
                "weight": 0.50,
                "article_count": mc_result[
                    "article_count"
                ],
                "status": mc_result[
                    "status"
                ],
                "articles": mc_result[
                    "articles"
                ],
            },
        },

        "timestamp": timestamp.isoformat(),
    }

    # ========================================================
    # Cache
    # ========================================================

    _sentiment_cache[cache_key] = {
        "data": result,
        "timestamp": timestamp,
    }

    logger.info(
        f"✅ Sentiment computed: "
        f"{label} ({weighted_score})"
    )

    return result


# ============================================================
# Cache Management
# ============================================================

def clear_sentiment_cache() -> None:
    """Clear all sentiment cache entries."""

    global _sentiment_cache

    _sentiment_cache = {}

    logger.info(
        "🗑️ Sentiment cache cleared."
    )