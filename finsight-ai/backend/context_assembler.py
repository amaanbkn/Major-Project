"""
FinSight AI — Context Assembler
Merges live data + RAG chunks + sentiment + query into a structured prompt
for Gemini Flash. This is the bridge between the orchestrator and the LLM.
"""

from datetime import datetime
from typing import Optional

from loguru import logger


def assemble_context(
    query: str,
    market_data: Optional[dict] = None,
    sentiment_data: Optional[dict] = None,
    signal_data: Optional[dict] = None,
    rag_chunks: Optional[list[dict]] = None,
    ipo_data: Optional[list[dict]] = None,
    portfolio_data: Optional[dict] = None,
    reasoning_steps: Optional[list[str]] = None,
) -> str:
    """
    Assemble a structured context prompt for Gemini Flash.

    Structure:
        [LIVE DATA] {market_snapshot}
        [SIGNALS] {technical_indicators}
        [SENTIMENT] {sentiment_scores}
        [KNOWLEDGE] {rag_chunks}
        [IPO DATA] {ipo_listings}
        [PORTFOLIO] {user_portfolio}
        [AGENT REASONING] {steps taken}
        [USER QUERY] {query}
    """
    sections = []

    # ── Timestamp ────────────────────────────────────────────
    sections.append(f"[TIMESTAMP] {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")

    # ── Live Market Data ─────────────────────────────────────
    if market_data:
        market_section = ["[LIVE DATA]"]
        if isinstance(market_data, dict):
            for key, value in market_data.items():
                if key not in ("status", "timestamp"):
                    market_section.append(f"  {key}: {value}")
        elif isinstance(market_data, list):
            for item in market_data[:10]:
                if isinstance(item, dict):
                    sym = item.get("symbol", "?")
                    price = item.get("price", "N/A")
                    change = item.get("change_pct", "N/A")
                    market_section.append(f"  {sym}: ₹{price} ({change}%)")
        sections.append("\n".join(market_section))

    # ── Technical Signals ────────────────────────────────────
    if signal_data:
        signal_section = ["[SIGNALS]"]
        if isinstance(signal_data, dict):
            signal_section.append(f"  Symbol: {signal_data.get('symbol', 'N/A')}")
            signal_section.append(f"  Signal: {signal_data.get('signal', 'N/A')}")
            signal_section.append(f"  Score: {signal_data.get('signal_score', 'N/A')}/3")
            indicators = signal_data.get("indicators", {})
            if indicators:
                signal_section.append(f"  RSI: {indicators.get('rsi', {}).get('value', 'N/A')}")
                signal_section.append(f"  SMA50: {indicators.get('sma_50', 'N/A')}")
                signal_section.append(f"  SMA200: {indicators.get('sma_200', 'N/A')}")
                signal_section.append(f"  MA Crossover: {indicators.get('ma_crossover', 'N/A')}")
            for analysis in signal_data.get("analysis", []):
                signal_section.append(f"  • {analysis}")
        sections.append("\n".join(signal_section))

    # ── Sentiment Data ───────────────────────────────────────
    if sentiment_data:
        sent_section = ["[SENTIMENT]"]
        sent_section.append(f"  Overall Score: {sentiment_data.get('overall_score', 'N/A')}")
        sent_section.append(f"  Label: {sentiment_data.get('overall_label', 'N/A')}")
        sources = sentiment_data.get("sources", {})
        for src_name, src_data in sources.items():
            if isinstance(src_data, dict):
                sent_section.append(f"  {src_name}: {src_data.get('score', 'N/A')} (weight: {src_data.get('weight', 'N/A')})")
                # Include top article headlines
                for article in src_data.get("articles", [])[:3]:
                    sent_section.append(f"    - {article.get('title', 'N/A')}")
                for post in src_data.get("posts", [])[:3]:
                    sent_section.append(f"    - {post.get('title', 'N/A')}")
        sections.append("\n".join(sent_section))

    # ── RAG Knowledge Chunks ─────────────────────────────────
    if rag_chunks:
        rag_section = ["[KNOWLEDGE]"]
        for i, chunk in enumerate(rag_chunks[:3]):
            text = chunk.get("text", "")[:500]  # Limit chunk size in prompt
            source = chunk.get("metadata", {}).get("doc_id", "unknown")
            distance = chunk.get("distance", "N/A")
            rag_section.append(f"  --- Chunk {i+1} (source: {source}, relevance: {round(1-distance, 2) if isinstance(distance, (int, float)) else 'N/A'}) ---")
            rag_section.append(f"  {text}")
        sections.append("\n".join(rag_section))

    # ── IPO Data ─────────────────────────────────────────────
    if ipo_data:
        ipo_section = ["[IPO DATA]"]
        for ipo in ipo_data[:5]:
            ipo_section.append(
                f"  {ipo.get('name', 'N/A')} | Price: {ipo.get('price_band', 'N/A')} | "
                f"GMP: {ipo.get('gmp', 'N/A')} | Dates: {ipo.get('open_date', '?')} - {ipo.get('close_date', '?')}"
            )
        sections.append("\n".join(ipo_section))

    # ── Portfolio Data ───────────────────────────────────────
    if portfolio_data:
        port_section = ["[PORTFOLIO]"]
        port_section.append(f"  Balance: ₹{portfolio_data.get('balance', 'N/A')}")
        holdings = portfolio_data.get("holdings", [])
        for h in holdings[:10]:
            port_section.append(
                f"  {h.get('symbol', '?')}: {h.get('quantity', 0)} shares @ ₹{h.get('buy_price', 0)} "
                f"(Current: ₹{h.get('current_price', 'N/A')})"
            )
        sections.append("\n".join(port_section))

    # ── Agent Reasoning Steps ────────────────────────────────
    if reasoning_steps:
        steps_section = ["[AGENT REASONING]"]
        for i, step in enumerate(reasoning_steps, 1):
            steps_section.append(f"  Step {i}: {step}")
        sections.append("\n".join(steps_section))

    # ── User Query ───────────────────────────────────────────
    sections.append(f"[USER QUERY] {query}")

    # ── Assemble ─────────────────────────────────────────────
    full_context = "\n\n".join(sections)

    logger.debug(f"Context assembled: {len(full_context)} characters, {len(sections)} sections")
    return full_context
