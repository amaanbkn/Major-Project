"""
FinSight AI — Gemini Client

Provides:
- Gemini text generation
- Gemini streaming text generation
- Intent classification
- Gemini embeddings for RAG
- Compatibility helper for existing application code
- Centralized system prompt
- Environment loading from backend/.env
- Error handling and logging
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from dotenv import load_dotenv
from loguru import logger

# ============================================================
# GOOGLE GENAI
# ============================================================

try:
    from google import genai
    from google.genai import types
except ImportError as exc:
    raise ImportError(
        "Google Gen AI SDK is not installed.\n"
        "Install it with:\n"
        "pip install -U google-genai"
    ) from exc


# ============================================================
# ENVIRONMENT
# ============================================================

# Current file:
# backend/services/gemini.py
#
# parents[0] -> backend/services
# parents[1] -> backend
#
# Therefore:
# backend/.env

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(
    ENV_FILE,
    override=True,
)

logger.info("🔧 Loading environment from: {}", ENV_FILE)
logger.info("📁 Environment file exists: {}", ENV_FILE.exists())


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
).strip()

# Default changed to the model your current API is accepting.
CHAT_MODEL = os.getenv(
    "GEMINI_CHAT_MODEL",
    "gemini-3.6-flash",
).strip()

EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-2",
).strip()


if GEMINI_API_KEY:
    logger.info("✅ Gemini API key loaded.")
else:
    logger.error(
        "❌ GEMINI_API_KEY is missing. Expected in: {}",
        ENV_FILE,
    )

logger.info("🤖 Chat model: {}", CHAT_MODEL)
logger.info("🧠 Embedding model: {}", EMBEDDING_MODEL)


# ============================================================
# CLIENT
# ============================================================

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """
    Return a singleton Gemini client.
    """
    global _client

    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured.\n"
                f"Expected environment file: {ENV_FILE}"
            )

        _client = genai.Client(
            api_key=GEMINI_API_KEY,
        )

        logger.info("✅ Gemini client initialized.")

    return _client


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are FinSight AI, an AI-powered market research assistant
for the Indian stock market.

Your purpose is to help retail investors understand financial
information using the evidence supplied by the application.

You can help users with:

- Indian stock market analysis
- Current stock prices and market trends
- RSI and moving-average interpretation
- Buy / Hold / Sell research signals
- Market sentiment
- Financial news interpretation
- IPO information and Grey Market Premium (GMP)
- SIP planning concepts
- Paper-trading portfolios
- Financial documents retrieved through RAG

IMPORTANT RULES:

1. Use application-provided live market context as the
   primary source for current information.

2. Never invent:
   - stock prices
   - IPO names
   - IPO GMP values
   - financial metrics
   - news
   - sentiment scores
   - technical indicators

3. If current information is unavailable, clearly state that
   the information is unavailable.

4. Distinguish factual market data from AI-generated analysis.

5. Explain important risks and uncertainty.

6. Never guarantee profits or future returns.

7. Never claim that a stock will definitely rise or fall.

8. Do not present an AI-generated Buy/Hold/Sell signal as a
   guaranteed investment outcome.

9. Keep responses understandable for retail investors.

10. Use Indian financial terminology and ₹ for Indian Rupee.

11. Grey Market Premium (GMP) is unofficial. Never present GMP
    as a guaranteed listing gain.

12. Do not use outdated model knowledge as a substitute for
    current market data supplied by the application.

13. When providing investment-related analysis, include:

    "AI-powered market research assistant — not financial advice."

14. This system is intended for educational and research
    purposes. Users should perform their own research and
    consult a SEBI-registered investment adviser before
    making investment decisions.
""".strip()


# ============================================================
# CHAT CONFIG
# ============================================================

def _chat_config(
    temperature: float = 0.4,
    max_output_tokens: int = 3000,
    system_instruction: Optional[str] = None,
) -> types.GenerateContentConfig:
    """
    Build Gemini generation configuration.

    No tools are supplied here, so automatic function calling
    is not used for normal FinSight responses.
    """

    return types.GenerateContentConfig(
        system_instruction=(
            system_instruction
            if system_instruction is not None
            else SYSTEM_PROMPT
        ),
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


# ============================================================
# COMPATIBILITY MODEL
# ============================================================

class GeminiModelCompat:
    """
    Compatibility wrapper for older application code.

    Existing code can continue using:

        model = get_chat_model()
        response = model.generate_content(prompt)
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
    ):
        self.model_name = (
            model_name or CHAT_MODEL
        )

    def generate_content(
        self,
        prompt: str,
    ):
        """
        Synchronous compatibility method.

        Uses the Chat API rather than the direct model call.
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        client = get_client()

        logger.info(
            "Generating compatibility response: {}",
            prompt[:100],
        )

        chat = client.chats.create(
            model=self.model_name,
            config=_chat_config(
                temperature=0.2,
                max_output_tokens=3000,
            ),
        )

        return chat.send_message(
            prompt.strip()
        )


def get_chat_model(
    model_name: Optional[str] = None,
) -> GeminiModelCompat:
    """
    Return compatibility wrapper for existing code.
    """
    return GeminiModelCompat(
        model_name=model_name,
    )


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_prompt(
    query: str,
    context: str = "",
) -> str:
    """
    Build the application prompt.

    The actual system instruction is also passed separately
    to Gemini. This function produces only the user-side
    content for the request.
    """

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    sections = [
        "=== USER QUERY ===",
        query.strip(),
    ]

    if context and context.strip():
        sections.extend(
            [
                "",
                "=== APPLICATION CONTEXT ===",
                context.strip(),
            ]
        )

    sections.extend(
        [
            "",
            "=== RESPONSE INSTRUCTIONS ===",
            "Answer the user's question directly.",
            "Use application-provided data whenever available.",
            "Do not fabricate missing financial information.",
            "Explicitly state when data is unavailable.",
            "Separate market facts from your interpretation.",
            "Include the financial disclaimer for investment-related analysis.",
        ]
    )

    return "\n".join(sections)


# ============================================================
# NORMAL ASYNC RESPONSE
# ============================================================

async def generate_response(
    query: str,
    context: str = "",
) -> str:
    """
    Generate a complete Gemini response asynchronously.

    Uses the official async Chat API.
    """

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    try:
        client = get_client()

        prompt = build_prompt(
            query=query,
            context=context,
        )

        logger.info(
            "🤖 Generating response: {}",
            query[:120],
        )

        chat = client.aio.chats.create(
            model=CHAT_MODEL,
            config=_chat_config(
                temperature=0.4,
                max_output_tokens=3000,
            ),
        )

        response = await chat.send_message(
            prompt
        )

        text = ""

        if response is not None:
            try:
                text = response.text or ""
            except Exception:
                text = ""

        text = text.strip()

        if not text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        logger.info(
            "✅ Gemini response generated ({} characters)",
            len(text),
        )

        return text

    except Exception as exc:
        logger.exception(
            "❌ Gemini response generation failed: {}",
            exc,
        )

        raise RuntimeError(
            f"Gemini generation failed: {exc}"
        ) from exc


# ============================================================
# STREAMING RESPONSE
# ============================================================

async def generate_streaming_response(
    query: str,
    context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream Gemini response asynchronously.

    Uses the official async Chat streaming API.
    """

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    prompt = build_prompt(
        query=query,
        context=context,
    )

    logger.info(
        "🚀 Starting Gemini streaming request: {}",
        query[:120],
    )

    try:
        client = get_client()

        chat = client.aio.chats.create(
            model=CHAT_MODEL,
            config=_chat_config(
                temperature=0.4,
                max_output_tokens=3000,
            ),
        )

        received_text = False

        # IMPORTANT:
        # google-genai's async streaming method returns an
        # async iterator after awaiting it.
        stream = await chat.send_message_stream(
            prompt
        )

        async for chunk in stream:
            if chunk is None:
                continue

            text = ""

            try:
                text = chunk.text or ""
            except Exception:
                text = ""

            if text:
                received_text = True
                yield text

        if not received_text:
            raise RuntimeError(
                "Gemini streaming completed without returning text."
            )

        logger.info(
            "✅ Gemini streaming completed successfully."
        )

    except Exception as exc:
        logger.exception(
            "❌ Gemini streaming failed: {}",
            exc,
        )

        raise RuntimeError(
            f"Gemini streaming failed: {exc}"
        ) from exc


# ============================================================
# EMBEDDING HELPERS
# ============================================================

def _prepare_embedding_query(
    text: str,
) -> str:
    """
    Prepare query text for semantic retrieval.
    """

    return (
        "task: search result | "
        f"query: {text.strip()}"
    )


def _prepare_embedding_document(
    text: str,
    title: Optional[str] = None,
) -> str:
    """
    Prepare document text for embedding.
    """

    safe_title = (
        title.strip()
        if title
        else "financial document"
    )

    return (
        f"title: {safe_title} | "
        f"text: {text.strip()}"
    )


# ============================================================
# SINGLE EMBEDDING
# ============================================================

async def get_embedding(
    text: str,
) -> list[float]:
    """
    Generate one Gemini embedding.
    """

    if not text or not text.strip():
        return []

    try:
        client = get_client()

        formatted_text = _prepare_embedding_query(
            text
        )

        result = await asyncio.to_thread(
            client.models.embed_content,
            model=EMBEDDING_MODEL,
            contents=formatted_text,
        )

        if not result:
            logger.warning(
                "⚠️ Gemini returned no embedding result."
            )
            return []

        embeddings = (
            result.embeddings or []
        )

        if not embeddings:
            logger.warning(
                "⚠️ Gemini returned no query embeddings."
            )
            return []

        first_embedding = embeddings[0]

        if first_embedding is None:
            return []

        values = first_embedding.values

        if not values:
            logger.warning(
                "⚠️ Gemini returned an empty query embedding."
            )
            return []

        return list(values)

    except Exception as exc:
        logger.exception(
            "❌ Query embedding generation failed: {}",
            exc,
        )
        return []


# ============================================================
# BATCH EMBEDDINGS
# ============================================================

async def get_embeddings_batch(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for a list of document chunks.

    Returned list preserves input ordering and length.
    """

    if not texts:
        return []

    valid_texts: list[str] = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not valid_texts:
        return [
            []
            for _ in texts
        ]

    try:
        client = get_client()

        formatted_documents = [
            _prepare_embedding_document(
                text
            )
            for text in valid_texts
        ]

        result = await asyncio.to_thread(
            client.models.embed_content,
            model=EMBEDDING_MODEL,
            contents=formatted_documents,
        )

        raw_embeddings = (
            result.embeddings
            if result
            else []
        )

        embeddings: list[list[float]] = []

        for embedding in raw_embeddings:
            if embedding is None:
                embeddings.append([])
                continue

            values = embedding.values

            if values:
                embeddings.append(
                    list(values)
                )
            else:
                embeddings.append([])

        if len(embeddings) != len(valid_texts):
            logger.error(
                "❌ Embedding count mismatch: expected {}, received {}",
                len(valid_texts),
                len(embeddings),
            )

            return [
                []
                for _ in texts
            ]

        # Restore original positions.
        result_embeddings: list[list[float]] = []

        valid_index = 0

        for text in texts:
            if not text or not text.strip():
                result_embeddings.append([])
            else:
                result_embeddings.append(
                    embeddings[valid_index]
                )
                valid_index += 1

        return result_embeddings

    except Exception as exc:
        logger.exception(
            "❌ Batch embedding generation failed: {}",
            exc,
        )

        return [
            []
            for _ in texts
        ]


# ============================================================
# INTENT CLASSIFICATION
# ============================================================

VALID_INTENTS = {
    "greeting",
    "stock_price",
    "stock_analysis",
    "market_sentiment",
    "ipo_info",
    "sip_advice",
    "paper_trade",
    "general_finance",
    "unknown",
}


KNOWN_SYMBOLS = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "BHARTIARTL",
    "ITC",
    "KOTAKBANK",
    "LT",
    "HINDUNILVR",
    "TATAMOTORS",
    "BAJFINANCE",
    "MARUTI",
    "WIPRO",
    "HCLTECH",
    "AXISBANK",
    "TITAN",
    "SUNPHARMA",
    "NTPC",
    "POWERGRID",
    "TATASTEEL",
    "JSWSTEEL",
    "ADANIENT",
    "ADANIPORTS",
    "BEL",
    "TRENT",
    "NIFTY",
    "SENSEX",
    "BANKNIFTY",
]


def _extract_symbols(
    query: str,
) -> list[str]:
    """
    Extract known Indian market symbols from text.
    """

    normalized = query.upper()

    symbols: list[str] = []

    for symbol in KNOWN_SYMBOLS:
        if re.search(
            rf"\b{re.escape(symbol)}\b",
            normalized,
        ):
            symbols.append(symbol)

    return symbols


def _heuristic_intent(
    query: str,
) -> Optional[dict[str, Any]]:
    """
    Fast intent classification for common queries.
    """

    cleaned = query.strip().lower()

    # --------------------------------------------------------
    # Greeting
    # --------------------------------------------------------

    if re.fullmatch(
        r"(hi|hello|hey|howdy|yo|sup|"
        r"thanks?|thank you|ok|okay|bye|"
        r"good morning|good afternoon|"
        r"good evening)",
        cleaned,
    ):
        return {
            "intent": "greeting",
            "symbols": [],
            "confidence": 1.0,
        }

    # --------------------------------------------------------
    # IPO
    # --------------------------------------------------------

    if any(
        term in cleaned
        for term in (
            "ipo",
            "gmp",
            "grey market",
            "grey market premium",
        )
    ):
        return {
            "intent": "ipo_info",
            "symbols": [],
            "confidence": 0.98,
        }

    # --------------------------------------------------------
    # SIP
    # --------------------------------------------------------

    if any(
        term in cleaned
        for term in (
            "sip",
            "mutual fund",
            "systematic investment",
            "monthly investment",
        )
    ):
        return {
            "intent": "sip_advice",
            "symbols": [],
            "confidence": 0.98,
        }

    # --------------------------------------------------------
    # Market sentiment
    # --------------------------------------------------------

    if any(
        term in cleaned
        for term in (
            "market mood",
            "market sentiment",
            "market outlook",
            "overall market",
            "market condition",
            "bullish market",
            "bearish market",
        )
    ):
        return {
            "intent": "market_sentiment",
            "symbols": [],
            "confidence": 0.98,
        }

    # --------------------------------------------------------
    # NIFTY
    # --------------------------------------------------------

    if (
        "nifty 50" in cleaned
        or "nifty50" in cleaned
        or cleaned == "nifty"
    ):
        return {
            "intent": "stock_price",
            "symbols": ["NIFTY"],
            "confidence": 0.98,
        }

    # --------------------------------------------------------
    # Paper trading
    # --------------------------------------------------------

    if re.search(
        r"\b(buy|sell)\b.*\b\d+\b.*"
        r"\b(share|shares|stock|stocks)\b",
        cleaned,
    ):
        return {
            "intent": "paper_trade",
            "symbols": _extract_symbols(query),
            "confidence": 0.98,
        }

    # --------------------------------------------------------
    # Known stock symbol + price keywords
    # --------------------------------------------------------

    symbols = _extract_symbols(query)

    if symbols:
        if any(
            word in cleaned
            for word in (
                "price",
                "current price",
                "latest price",
                "today price",
                "share price",
                "stock price",
            )
        ):
            return {
                "intent": "stock_price",
                "symbols": symbols,
                "confidence": 0.95,
            }

        if any(
            word in cleaned
            for word in (
                "analysis",
                "technical",
                "rsi",
                "moving average",
                "buy",
                "hold",
                "sell",
                "target",
                "trend",
                "should i invest",
                "should i buy",
            )
        ):
            return {
                "intent": "stock_analysis",
                "symbols": symbols,
                "confidence": 0.95,
            }

    return None


async def classify_intent(
    query: str,
) -> dict[str, Any]:
    """
    Classify user intent using:
    1. Fast heuristics
    2. Gemini fallback
    """

    if not query or not query.strip():
        return {
            "intent": "unknown",
            "symbols": [],
            "confidence": 0.0,
        }

    # ========================================================
    # HEURISTIC
    # ========================================================

    heuristic = _heuristic_intent(
        query
    )

    if heuristic:
        logger.debug(
            "Intent classified heuristically: {}",
            heuristic,
        )
        return heuristic

    detected_symbols = _extract_symbols(
        query
    )

    # ========================================================
    # GEMINI FALLBACK
    # ========================================================

    classification_system_prompt = """
You classify user queries for FinSight AI,
an Indian financial assistant.

Return ONLY valid JSON.

Allowed intents:

greeting
stock_price
stock_analysis
market_sentiment
ipo_info
sip_advice
paper_trade
general_finance
unknown

Definitions:

greeting:
Casual greeting, thanks, or simple conversation.

stock_price:
Asking for current/latest price of a specific stock.

stock_analysis:
Asking for stock analysis, technical analysis,
buy/hold/sell research, or investment research.

market_sentiment:
Asking about overall Indian market mood or sentiment.

ipo_info:
Asking about IPOs, IPO calendar, GMP,
subscription, or IPO evaluation.

sip_advice:
Asking about SIPs, mutual funds, monthly investing,
risk appetite, or investment goals.

paper_trade:
Asking to buy or sell shares using a virtual
paper-trading portfolio.

general_finance:
General finance or investment education.

unknown:
Not related to finance.
""".strip()

    prompt = f"""
Detected symbols:
{detected_symbols}

User query:
{query}

Return exactly this JSON structure:

{{
  "intent": "greeting|stock_price|stock_analysis|market_sentiment|ipo_info|sip_advice|paper_trade|general_finance|unknown",
  "symbols": [],
  "confidence": 0.0
}}
""".strip()

    try:
        client = get_client()

        chat = client.aio.chats.create(
            model=CHAT_MODEL,
            config=_chat_config(
                temperature=0.0,
                max_output_tokens=300,
                system_instruction=classification_system_prompt,
            ),
        )

        response = await chat.send_message(
            prompt
        )

        text = ""

        if response is not None:
            try:
                text = response.text or ""
            except Exception:
                text = ""

        text = text.strip()

        if not text:
            raise ValueError(
                "Gemini returned an empty intent response."
            )

        # Remove markdown JSON fences.
        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"^```\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        parsed = json.loads(
            text
        )

        # ----------------------------------------------------
        # Validate intent
        # ----------------------------------------------------

        if parsed.get("intent") not in VALID_INTENTS:
            parsed["intent"] = "general_finance"

        # ----------------------------------------------------
        # Validate symbols
        # ----------------------------------------------------

        if not isinstance(
            parsed.get("symbols"),
            list,
        ):
            parsed["symbols"] = []

        if (
            not parsed["symbols"]
            and detected_symbols
        ):
            parsed["symbols"] = detected_symbols

        parsed["symbols"] = [
            str(symbol).upper().strip()
            for symbol in parsed["symbols"]
            if symbol
        ]

        # ----------------------------------------------------
        # Validate confidence
        # ----------------------------------------------------

        try:
            parsed["confidence"] = max(
                0.0,
                min(
                    1.0,
                    float(
                        parsed.get(
                            "confidence",
                            0.5,
                        )
                    ),
                ),
            )
        except (
            TypeError,
            ValueError,
        ):
            parsed["confidence"] = 0.5

        logger.info(
            "✅ Gemini intent: {}",
            parsed,
        )

        return parsed

    except Exception as exc:
        logger.warning(
            "⚠️ Gemini intent classification failed: {}",
            exc,
        )

        # Safe fallback.
        if detected_symbols:
            return {
                "intent": "stock_analysis",
                "symbols": detected_symbols,
                "confidence": 0.5,
            }

        return {
            "intent": "general_finance",
            "symbols": [],
            "confidence": 0.5,
        }


# ============================================================
# GEMINI STATUS
# ============================================================

def get_gemini_status() -> dict[str, Any]:
    """
    Return Gemini configuration information
    without exposing the API key.
    """

    return {
        "configured": bool(
            GEMINI_API_KEY
        ),
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "env_file": str(
            ENV_FILE
        ),
        "env_exists": ENV_FILE.exists(),
    }