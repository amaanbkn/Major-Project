"""
FinSight AI — Context Assembler

Combines:
- Live market data
- Technical signals
- Financial-news sentiment
- IPO information
- User portfolio information
- RAG-retrieved financial knowledge
- User query

into a structured context for the Gemini model.

Important:
This module prepares evidence for Gemini.
It does NOT make independent financial decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from loguru import logger


IST = ZoneInfo("Asia/Kolkata")


def _safe_value(value: Any, default: str = "N/A") -> str:
    """Convert a value to a safe printable string."""
    if value is None:
        return default

    if isinstance(value, str) and not value.strip():
        return default

    return str(value)


def _format_number(
    value: Any,
    decimals: int = 2,
    default: str = "N/A",
) -> str:
    """Safely format numeric values."""
    if value is None:
        return default

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return default


def _format_relevance(distance: Any) -> str:
    """
    Convert a Chroma distance into a human-readable relevance score.

    Important:
    ChromaDB distance semantics depend on the configured metric.
    We therefore avoid presenting 1-distance as an absolute truth.

    The raw distance is included so the LLM can treat it as retrieval
    metadata rather than a false precision score.
    """
    if distance is None:
        return "N/A"

    try:
        value = float(distance)
    except (TypeError, ValueError):
        return "N/A"

    return f"{value:.4f}"


def _append_section(
    sections: list[str],
    title: str,
    lines: list[str],
) -> None:
    """Append a section only when it contains useful information."""
    if not lines:
        return

    sections.append(
        "\n".join(
            [title] + [f"  {line}" for line in lines]
        )
    )


def assemble_context(
    query: str,
    market_data: Optional[dict | list[dict]] = None,
    sentiment_data: Optional[dict] = None,
    signal_data: Optional[dict | list[dict]] = None,
    rag_chunks: Optional[list[dict]] = None,
    ipo_data: Optional[list[dict]] = None,
    portfolio_data: Optional[dict] = None,
    reasoning_steps: Optional[list[str]] = None,
) -> str:
    """
    Build structured evidence context for Gemini.

    Context sections:
        [SYSTEM CONTEXT]
        [TIMESTAMP]
        [LIVE MARKET DATA]
        [TECHNICAL SIGNALS]
        [MARKET SENTIMENT]
        [IPO DATA]
        [RAG KNOWLEDGE]
        [USER PORTFOLIO]
        [PROCESSING SUMMARY]
        [USER QUERY]
        [RESPONSE RULES]

    The output is intentionally explicit so Gemini can distinguish
    real-time evidence from retrieved background knowledge.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    sections: list[str] = []

    # ==========================================================
    # System Context
    # ==========================================================

    sections.append(
        "[SYSTEM CONTEXT]\n"
        "FinSight AI is an AI-powered market research and "
        "decision-support assistant for Indian retail investors."
    )

    # ==========================================================
    # Timestamp
    # ==========================================================

    current_time = datetime.now(IST)

    sections.append(
        "[TIMESTAMP]\n"
        f"  Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    # ==========================================================
    # Live Market Data
    # ==========================================================

    if market_data:
        lines: list[str] = []

        if isinstance(market_data, dict):

            # Common index/stock fields.
            preferred_keys = [
                "symbol",
                "name",
                "value",
                "price",
                "last_price",
                "change",
                "change_pct",
                "open",
                "high",
                "low",
                "previous_close",
                "volume",
                "pe",
                "eps",
                "market_cap",
                "52w_high",
                "52w_low",
                "timestamp",
                "source",
            ]

            added_keys: set[str] = set()

            for key in preferred_keys:
                if key not in market_data:
                    continue

                value = market_data.get(key)

                if value is None:
                    continue

                lines.append(
                    f"{key}: {_safe_value(value)}"
                )
                added_keys.add(key)

            # Include any additional fields not already handled.
            for key, value in market_data.items():
                if key in added_keys:
                    continue

                if value is None:
                    continue

                if isinstance(value, (dict, list)):
                    continue

                lines.append(
                    f"{key}: {_safe_value(value)}"
                )

        elif isinstance(market_data, list):

            for item in market_data[:10]:
                if not isinstance(item, dict):
                    continue

                symbol = _safe_value(
                    item.get("symbol"),
                    "?",
                )

                name = _safe_value(
                    item.get("name"),
                    "",
                )

                price = _safe_value(
                    item.get("price", item.get("value")),
                )

                change_pct = _safe_value(
                    item.get("change_pct"),
                )

                if name and name != "N/A":
                    lines.append(
                        f"{symbol} ({name}) | "
                        f"Price: ₹{price} | "
                        f"Change: {change_pct}%"
                    )
                else:
                    lines.append(
                        f"{symbol} | "
                        f"Price: ₹{price} | "
                        f"Change: {change_pct}%"
                    )

        _append_section(
            sections,
            "[LIVE MARKET DATA]",
            lines,
        )

    # ==========================================================
    # Technical Signals
    # ==========================================================

    if signal_data:
        lines = []

        signal_items: list[dict]

        if isinstance(signal_data, dict):
            signal_items = [signal_data]
        else:
            signal_items = [
                item
                for item in signal_data
                if isinstance(item, dict)
            ]

        for item in signal_items[:10]:

            symbol = _safe_value(
                item.get("symbol"),
                "?",
            )

            signal = _safe_value(
                item.get("signal"),
            )

            score = _safe_value(
                item.get("signal_score"),
            )

            lines.append(
                f"Symbol: {symbol}"
            )

            lines.append(
                f"Signal: {signal}"
            )

            lines.append(
                f"Signal score: {score}"
            )

            indicators = item.get(
                "indicators",
                {},
            )

            if isinstance(indicators, dict):

                rsi_data = indicators.get(
                    "rsi",
                    {},
                )

                if isinstance(rsi_data, dict):
                    rsi_value = rsi_data.get(
                        "value"
                    )
                else:
                    rsi_value = rsi_data

                lines.append(
                    f"RSI: {_format_number(rsi_value)}"
                )

                lines.append(
                    f"SMA 50: {_format_number(indicators.get('sma_50'))}"
                )

                lines.append(
                    f"SMA 200: {_format_number(indicators.get('sma_200'))}"
                )

                lines.append(
                    f"MA crossover: "
                    f"{_safe_value(indicators.get('ma_crossover'))}"
                )

            analysis = item.get(
                "analysis",
                [],
            )

            if isinstance(analysis, list):
                for explanation in analysis[:5]:
                    if explanation:
                        lines.append(
                            f"Analysis: {explanation}"
                        )

        _append_section(
            sections,
            "[TECHNICAL SIGNALS]",
            lines,
        )

    # ==========================================================
    # Market Sentiment
    # ==========================================================

    if sentiment_data:
        lines = []

        overall_score = sentiment_data.get(
            "overall_score"
        )

        overall_label = sentiment_data.get(
            "overall_label"
        )

        lines.append(
            f"Overall sentiment score: "
            f"{_safe_value(overall_score)}"
        )

        lines.append(
            f"Overall sentiment: "
            f"{_safe_value(overall_label)}"
        )

        sources = sentiment_data.get(
            "sources",
            {},
        )

        if isinstance(sources, dict):

            for source_name, source_data in sources.items():

                if not isinstance(
                    source_data,
                    dict,
                ):
                    continue

                source_score = source_data.get(
                    "score"
                )

                weight = source_data.get(
                    "weight"
                )

                lines.append(
                    f"{source_name}: "
                    f"score={_safe_value(source_score)}, "
                    f"weight={_safe_value(weight)}"
                )

                # Financial news only.
                articles = source_data.get(
                    "articles",
                    [],
                )

                if isinstance(articles, list):

                    for article in articles[:3]:

                        if not isinstance(
                            article,
                            dict,
                        ):
                            continue

                        title = article.get(
                            "title"
                        )

                        published = (
                            article.get("published_at")
                            or article.get("published")
                            or article.get("pubDate")
                        )

                        if title:
                            news_line = (
                                f"News: {title}"
                            )

                            if published:
                                news_line += (
                                    f" | Published: {published}"
                                )

                            lines.append(
                                news_line
                            )

        _append_section(
            sections,
            "[MARKET SENTIMENT]",
            lines,
        )

    # ==========================================================
    # IPO Data
    # ==========================================================

    if ipo_data is not None:
        lines = []

        if not ipo_data:
            lines.append(
                "Current IPO information is unavailable. "
                "Live sources returned no IPO records. "
                "Do not invent IPO names, dates, price bands, or GMP."
            )
        else:
            for ipo in ipo_data[:10]:

                if not isinstance(ipo, dict):
                    continue

                name = _safe_value(
                    ipo.get("name"),
                    "Unknown IPO",
                )

                price_band = _safe_value(
                    ipo.get("price_band"),
                )

                gmp = _safe_value(
                    ipo.get("gmp"),
                )

                open_date = _safe_value(
                    ipo.get("open_date"),
                    "?",
                )

                close_date = _safe_value(
                    ipo.get("close_date"),
                    "?",
                )

                status = _safe_value(
                    ipo.get("status"),
                )

                subscription = _safe_value(
                    ipo.get("subscription"),
                    ipo.get("subscription_times"),
                )

                line = (
                    f"{name} | "
                    f"Price band: {price_band} | "
                    f"GMP: {gmp} | "
                    f"Open: {open_date} | "
                    f"Close: {close_date} | "
                    f"Status: {status}"
                )

                if subscription != "N/A":
                    line += (
                        f" | Subscription: {subscription}"
                    )

                lines.append(line)

        _append_section(
            sections,
            "[IPO DATA]",
            lines,
        )

    # ==========================================================
    # RAG Knowledge
    # ==========================================================

    if rag_chunks:
        lines = []

        for index, chunk in enumerate(
            rag_chunks[:3],
            start=1,
        ):

            if not isinstance(
                chunk,
                dict,
            ):
                continue

            text = str(
                chunk.get("text")
                or chunk.get("document")
                or ""
            ).strip()

            if not text:
                continue

            metadata = chunk.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            source = (
                metadata.get("doc_id")
                or metadata.get("source")
                or metadata.get("filename")
                or "unknown"
            )

            distance = chunk.get(
                "distance"
            )

            lines.append(
                f"Chunk {index} | "
                f"Source: {source} | "
                f"Retrieval distance: "
                f"{_format_relevance(distance)}"
            )

            # Keep individual chunks bounded.
            lines.append(
                f"Content: {text[:1200]}"
            )

        _append_section(
            sections,
            "[RAG KNOWLEDGE]",
            lines,
        )

    # ==========================================================
    # Portfolio
    # ==========================================================

    if portfolio_data:
        lines = []

        balance = portfolio_data.get(
            "balance"
        )

        lines.append(
            f"Available virtual balance: "
            f"₹{_safe_value(balance)}"
        )

        holdings = portfolio_data.get(
            "holdings",
            [],
        )

        if isinstance(
            holdings,
            list,
        ):

            for holding in holdings[:10]:

                if not isinstance(
                    holding,
                    dict,
                ):
                    continue

                symbol = _safe_value(
                    holding.get("symbol"),
                    "?",
                )

                quantity = _safe_value(
                    holding.get("quantity"),
                    "0",
                )

                buy_price = _safe_value(
                    holding.get("buy_price"),
                )

                current_price = _safe_value(
                    holding.get("current_price"),
                )

                lines.append(
                    f"{symbol}: "
                    f"{quantity} shares | "
                    f"Average buy price: ₹{buy_price} | "
                    f"Current price: ₹{current_price}"
                )

        _append_section(
            sections,
            "[USER PAPER-TRADING PORTFOLIO]",
            lines,
        )

    # ==========================================================
    # Processing Summary
    # ==========================================================
    #
    # Do not present internal reasoning as financial evidence.
    # Keep it as a lightweight processing summary.

    if reasoning_steps:
        cleaned_steps = []

        for step in reasoning_steps:

            if not step:
                continue

            cleaned = str(step).strip()

            if cleaned:
                cleaned_steps.append(cleaned)

        if cleaned_steps:
            sections.append(
                "[PROCESSING SUMMARY]\n"
                "  The system performed the following analysis steps:\n"
                + "\n".join(
                    f"  - {step}"
                    for step in cleaned_steps[-8:]
                )
            )

    # ==========================================================
    # User Query
    # ==========================================================

    sections.append(
        "[USER QUERY]\n"
        f"  {query.strip()}"
    )

    # ==========================================================
    # Response Rules
    # ==========================================================

    sections.append(
        "[RESPONSE RULES]\n"
        "  1. Answer the user query directly and clearly.\n"
        "  2. Treat LIVE MARKET DATA as the most time-sensitive evidence.\n"
        "  3. Treat RAG KNOWLEDGE as supplementary background information.\n"
        "  4. Do not invent stock prices, IPO details, news, sentiment scores, or financial metrics.\n"
        "  5. When a required value is unavailable, explicitly say that it is unavailable.\n"
        "  6. Distinguish factual data from AI-generated interpretation.\n"
        "  7. Explain important risks and uncertainties.\n"
        "  8. Do not guarantee returns or future market movements.\n"
        "  9. For investment-related questions, include the disclaimer:\n"
        "     'AI-powered market research assistant — not financial advice.'\n"
        "  10. Use Indian financial terminology and ₹ for amounts.\n"
        "  11. Do not treat IPO GMP as a guaranteed listing gain.\n"
        "  12. Never imply that an AI-generated signal guarantees a profitable trade."
    )

    # ==========================================================
    # Final Assembly
    # ==========================================================

    full_context = "\n\n".join(sections)

    logger.debug(
        "Context assembled: "
        f"{len(full_context)} characters, "
        f"{len(sections)} sections"
    )

    return full_context