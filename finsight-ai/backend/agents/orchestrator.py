"""
FinSight AI — Agentic Orchestrator
Central coordinator that:
1. Parses user intent from query (via Gemini)
2. Decides which tools to invoke
3. Collects evidence from all relevant tools (async)
4. Passes assembled context to context_assembler.py
5. Calls Gemini Flash for final response
6. Exposes "reasoning steps" for frontend transparency
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional

from loguru import logger


class OrchestratorResult:
    """Container for orchestrator results including reasoning steps."""

    def __init__(self):
        self.reasoning_steps: list[str] = []
        self.market_data: Optional[dict] = None
        self.signal_data: Optional[dict] = None
        self.sentiment_data: Optional[dict] = None
        self.rag_chunks: Optional[list[dict]] = None
        self.ipo_data: Optional[list[dict]] = None
        self.portfolio_data: Optional[dict] = None
        self.context: str = ""
        self.response: str = ""
        self.intent: dict = {}

    def add_step(self, step: str):
        self.reasoning_steps.append(step)
        logger.info(f"🔧 Agent step: {step}")

    def to_dict(self) -> dict:
        return {
            "reasoning_steps": self.reasoning_steps,
            "intent": self.intent,
            "context_length": len(self.context),
            "response": self.response,
            "timestamp": datetime.now().isoformat(),
        }


# ── Tool registry ────────────────────────────────────────────
TOOL_MAP = {
    "fetch_price": "Fetch live stock price",
    "get_signal": "Compute technical Buy/Hold/Sell signal",
    "get_sentiment": "Analyze market sentiment",
    "retrieve_rag": "Search knowledge base (DRHP, SEBI docs)",
    "get_ipo": "Fetch IPO calendar and GMP",
    "get_portfolio": "Retrieve user portfolio",
    "get_nifty": "Fetch NIFTY 50 index data",
}


async def orchestrate(query: str, user_id: str = "default") -> OrchestratorResult:
    """
    Main orchestration pipeline:
    1. Classify user intent
    2. Route to appropriate tools
    3. Assemble context
    4. Generate response

    Returns OrchestratorResult with response, reasoning steps, and all data.
    """
    result = OrchestratorResult()
    result.add_step(f"Received query: '{query[:80]}...' " if len(query) > 80 else f"Received query: '{query}'")

    # ── Step 1: Intent Classification ────────────────────────
    result.add_step("Classifying user intent via Gemini...")
    from services.gemini import classify_intent
    intent = await classify_intent(query)
    result.intent = intent
    result.add_step(f"Intent: {intent.get('intent', 'unknown')} | Symbols: {intent.get('symbols', [])}")

    # ── Step 2: Route to tools based on intent ───────────────
    tasks = []
    intent_type = intent.get("intent", "general_finance")
    symbols = intent.get("symbols", [])

    # Always try RAG for financial queries
    if intent_type not in ("greeting", "unknown"):
        tasks.append(("retrieve_rag", _tool_retrieve_rag(query)))
        result.add_step("🔍 Searching knowledge base for relevant documents...")

    # Stock-related intents
    if intent_type in ("stock_price", "stock_analysis") and symbols:
        for sym in symbols:
            tasks.append(("fetch_price", _tool_fetch_price(sym)))
            result.add_step(f"📊 Fetching live price for {sym}...")

        if intent_type == "stock_analysis":
            for sym in symbols:
                tasks.append(("get_signal", _tool_get_signal(sym)))
                result.add_step(f"📈 Computing technical signals for {sym}...")

            tasks.append(("get_sentiment", _tool_get_sentiment()))
            result.add_step("📰 Analyzing market sentiment...")

    # Market sentiment intent
    elif intent_type == "market_sentiment":
        tasks.append(("get_sentiment", _tool_get_sentiment()))
        result.add_step("📰 Fetching sentiment from ET, Moneycontrol, Reddit...")
        tasks.append(("get_nifty", _tool_get_nifty()))
        result.add_step("📊 Fetching NIFTY 50 index...")

    # IPO intent
    elif intent_type == "ipo_info":
        tasks.append(("get_ipo", _tool_get_ipo()))
        result.add_step("📋 Fetching IPO calendar and GMP data...")

    # Paper trading intent
    elif intent_type == "paper_trade":
        if symbols:
            for sym in symbols:
                tasks.append(("fetch_price", _tool_fetch_price(sym)))
                result.add_step(f"📊 Fetching price for {sym} (paper trade)...")
        tasks.append(("get_portfolio", _tool_get_portfolio(user_id)))
        result.add_step("💼 Loading portfolio data...")

    # SIP advice
    elif intent_type == "sip_advice":
        tasks.append(("get_sentiment", _tool_get_sentiment()))
        result.add_step("📈 Analyzing market conditions for SIP recommendation...")

    # General finance — just RAG is enough (already added above)
    elif intent_type == "general_finance":
        tasks.append(("get_nifty", _tool_get_nifty()))
        result.add_step("📊 Fetching market overview...")

    # Greeting — no tools needed
    elif intent_type == "greeting":
        result.add_step("👋 Greeting detected — responding directly")
        result.response = (
            "Hello! I'm FinSight AI, your market research assistant. "
            "You can ask me about Indian stocks, SIP recommendations, "
            "upcoming IPOs, or market sentiment. What would you like to know?"
        )
        return result

    # ── Step 3: Execute all tools concurrently ───────────────
    if tasks:
        result.add_step(f"⚡ Executing {len(tasks)} tools concurrently...")
        tool_results = await asyncio.gather(
            *[task[1] for task in tasks],
            return_exceptions=True,
        )

        # Process results
        for (tool_name, _), tool_result in zip(tasks, tool_results):
            if isinstance(tool_result, Exception):
                result.add_step(f"⚠️ Tool '{tool_name}' failed: {str(tool_result)}")
                continue

            if tool_name == "fetch_price":
                result.market_data = tool_result
                result.add_step(f"✅ Price data received: ₹{tool_result.get('price', 'N/A')}")
            elif tool_name == "get_signal":
                result.signal_data = tool_result
                result.add_step(f"✅ Signal: {tool_result.get('signal', 'N/A')}")
            elif tool_name == "get_sentiment":
                result.sentiment_data = tool_result
                result.add_step(f"✅ Sentiment: {tool_result.get('overall_label', 'N/A')} ({tool_result.get('overall_score', 0)})")
            elif tool_name == "retrieve_rag":
                result.rag_chunks = tool_result
                result.add_step(f"✅ Retrieved {len(tool_result) if tool_result else 0} knowledge chunks")
            elif tool_name == "get_ipo":
                result.ipo_data = tool_result
                result.add_step(f"✅ Got {len(tool_result) if tool_result else 0} IPO listings")
            elif tool_name == "get_portfolio":
                result.portfolio_data = tool_result
                result.add_step(f"✅ Portfolio loaded: ₹{tool_result.get('balance', 'N/A')} balance")
            elif tool_name == "get_nifty":
                if not result.market_data:
                    result.market_data = tool_result
                result.add_step(f"✅ NIFTY 50: {tool_result.get('value', 'N/A')}")

    # ── Step 4: Assemble context ─────────────────────────────
    result.add_step("🔨 Assembling context for Gemini...")
    from context_assembler import assemble_context
    result.context = assemble_context(
        query=query,
        market_data=result.market_data,
        sentiment_data=result.sentiment_data,
        signal_data=result.signal_data,
        rag_chunks=result.rag_chunks,
        ipo_data=result.ipo_data,
        portfolio_data=result.portfolio_data,
        reasoning_steps=result.reasoning_steps,
    )
    result.add_step(f"📝 Context ready: {len(result.context)} characters")

    # ── Step 5: Generate response via Gemini ─────────────────
    result.add_step("🤖 Generating response via Gemini 1.5 Flash...")
    from services.gemini import generate_response
    result.response = await generate_response(query, context=result.context)
    result.add_step("✅ Response generated successfully")

    return result


async def orchestrate_streaming(
    query: str,
    user_id: str = "default",
) -> AsyncGenerator[dict, None]:
    """
    Streaming orchestration: yields events for real-time frontend display.
    Event types: 'step', 'chunk', 'data', 'done', 'error'
    """
    reasoning_steps = []

    def add_step(step: str):
        reasoning_steps.append(step)
        logger.info(f"🔧 Agent step: {step}")

    try:
        # Step 1: Intent
        add_step("Classifying user intent...")
        yield {"type": "step", "content": "Classifying user intent..."}

        from services.gemini import classify_intent
        intent = await classify_intent(query)
        add_step(f"Intent: {intent.get('intent', 'unknown')}")
        yield {"type": "step", "content": f"Intent: {intent.get('intent', 'unknown')} | Symbols: {intent.get('symbols', [])}"}

        # Step 2: Execute tools
        intent_type = intent.get("intent", "general_finance")
        symbols = intent.get("symbols", [])
        context_data = {}

        if intent_type == "greeting":
            yield {"type": "chunk", "content": "Hello! I'm FinSight AI 👋 Ask me about any Indian stock, SIP, IPO, or market sentiment."}
            yield {"type": "done", "content": ""}
            return

        # Gather tools based on intent
        if intent_type in ("stock_price", "stock_analysis") and symbols:
            for sym in symbols:
                yield {"type": "step", "content": f"Fetching live data for {sym}..."}
                price = await _tool_fetch_price(sym)
                context_data["market_data"] = price
                yield {"type": "data", "content": {"price": price}}

            if intent_type == "stock_analysis":
                for sym in symbols:
                    yield {"type": "step", "content": f"Computing signals for {sym}..."}
                    signal = await _tool_get_signal(sym)
                    context_data["signal_data"] = signal

                yield {"type": "step", "content": "Analyzing sentiment..."}
                sentiment = await _tool_get_sentiment()
                context_data["sentiment_data"] = sentiment

        elif intent_type == "market_sentiment":
            yield {"type": "step", "content": "Analyzing market sentiment..."}
            sentiment = await _tool_get_sentiment()
            context_data["sentiment_data"] = sentiment

        elif intent_type == "ipo_info":
            yield {"type": "step", "content": "Fetching IPO data..."}
            ipo = await _tool_get_ipo()
            context_data["ipo_data"] = ipo

        elif intent_type == "paper_trade":
            if symbols:
                for sym in symbols:
                    price = await _tool_fetch_price(sym)
                    context_data["market_data"] = price
            portfolio = await _tool_get_portfolio(user_id)
            context_data["portfolio_data"] = portfolio

        # RAG for all non-greeting queries
        if intent_type not in ("greeting",):
            yield {"type": "step", "content": "Searching knowledge base..."}
            rag = await _tool_retrieve_rag(query)
            context_data["rag_chunks"] = rag

        # Step 3: Assemble context
        yield {"type": "step", "content": "Assembling context..."}
        from context_assembler import assemble_context
        context = assemble_context(query=query, reasoning_steps=reasoning_steps, **context_data)

        # Step 4: Stream response
        yield {"type": "step", "content": "Generating response..."}
        from services.gemini import generate_streaming_response
        async for chunk in generate_streaming_response(query, context=context):
            yield {"type": "chunk", "content": chunk}

        yield {"type": "done", "content": ""}

    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        yield {"type": "error", "content": str(e)}


# ── Tool wrapper functions ───────────────────────────────────

async def _tool_fetch_price(symbol: str) -> dict:
    from services.market_data import get_stock_price
    return await get_stock_price(symbol)


async def _tool_get_signal(symbol: str) -> dict:
    from services.signals_engine import compute_signals
    return await compute_signals(symbol)


async def _tool_get_sentiment() -> dict:
    from services.sentiment import get_market_sentiment
    return await get_market_sentiment()


async def _tool_retrieve_rag(query: str) -> list[dict]:
    from services.rag import retrieve_relevant
    return await retrieve_relevant(query, top_k=3)


async def _tool_get_ipo() -> list[dict]:
    from services.ipo_tracker import get_upcoming_ipos
    return await get_upcoming_ipos()


async def _tool_get_portfolio(user_id: str) -> dict:
    from trading_engine import get_portfolio
    return await get_portfolio(user_id)


async def _tool_get_nifty() -> dict:
    from services.market_data import get_nifty_index
    return await get_nifty_index()
