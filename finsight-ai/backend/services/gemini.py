"""
FinSight AI — Gemini Flash Client
Handles all interactions with Google Gemini 1.5 Flash:
  - Streaming text generation
  - Text embeddings (text-embedding-004)
  - System prompt construction
"""

import os
from typing import AsyncGenerator, Optional

# pyrefly: ignore [missing-import]
import google.generativeai as genai
# pyrefly: ignore [missing-import]
from loguru import logger

# ── Configure Gemini ─────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# ── Model instances (Singleton pattern) ─────────────────────
_chat_model = None
_embedding_model = "models/gemini-embedding-2"
_embedding_model = "models/gemini-embedding-2"
MODEL_CANDIDATES = [
    "gemini-flash-lite-latest",      # cheapest/fastest — try first
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",           # alias fallback
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

SYSTEM_PROMPT = """You are FinSight AI, a sophisticated market research assistant built for the Indian stock market.

**Your capabilities:**
- Analyze live stock prices, technical indicators (RSI, Moving Averages), and market trends
- Provide weighted sentiment analysis from Economic Times and Moneycontrol
- Retrieve relevant financial knowledge from DRHP prospectuses, SEBI circulars, and RBI documents
- Track IPO calendars, Grey Market Premiums, and subscription data
- Recommend SIP strategies based on risk profiling
- Simulate paper trading with virtual portfolios

**Important guidelines:**
- Always cite the data sources you used in your analysis
- Present data in clear, structured formats with tables when appropriate
- Use ₹ symbol for Indian Rupee amounts
- When discussing specific stocks, include relevant metrics (PE ratio, market cap, etc.)
- Highlight both opportunities AND risks in any analysis

**DISCLAIMER:** This is an AI-assisted tool for educational and research purposes only. 
The information provided does not constitute financial advice. Always consult a SEBI-registered 
investment advisor before making investment decisions. Past performance is not indicative of 
future results. {SEBI Disclaimer as per SEBI (Investment Advisers) Regulations, 2013}"""


def get_chat_model(model_name: str = None):
    """Get or create the Gemini chat model."""
    target_name = model_name or MODEL_CANDIDATES[0]
    return genai.GenerativeModel(
        model_name=target_name,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=4096,
        ),
    )


async def generate_response(query: str, context: str = "") -> str:
    """
    Generate a non-streaming response from Gemini with fallback across candidate models.
    """
    full_prompt = f"{context}\n\nRespond to the [USER QUERY] above." if context else query
    
    last_error = None
    for candidate in MODEL_CANDIDATES:
        try:
            model = get_chat_model(candidate)
            response = model.generate_content(full_prompt)
            if response.text:
                return response.text
        except Exception as e:
            logger.warning(f"Model {candidate} failed ({e}), trying next candidate...")
            last_error = e
            continue

    logger.error(f"All Gemini candidates failed: {last_error}")
    return f"I apologize, but I encountered an error processing your request: {str(last_error)}"


async def generate_streaming_response(
    prompt: str,
    context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response from Gemini with automatic candidate model fallback.
    Yields text chunks as they arrive.
    """
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    
    streamed_anything = False
    last_error = None

    for candidate in MODEL_CANDIDATES:
        try:
            model = get_chat_model(candidate)
            response = model.generate_content(full_prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    streamed_anything = True
                    yield chunk.text

            if streamed_anything:
                return
        except Exception as e:
            logger.warning(f"Streaming candidate {candidate} failed: {e}")
            last_error = e
            if streamed_anything:
                # If we already sent partial tokens, yield error and stop
                yield f"\n\n⚠️ Error during stream: {str(e)}"
                return
            # Otherwise try the next candidate model
            continue

    if not streamed_anything:
        logger.error(f"All Gemini streaming candidates failed: {last_error}")
        yield f"\n\n⚠️ All AI models are currently rate-limited. Please wait a few moments and try again."


async def get_embedding(text: str) -> list[float]:
    """
    Get embedding vector for a text using text-embedding-004.
    Used for RAG: query embedding and document chunk embedding.
    """
    try:
        result = genai.embed_content(
            model=_embedding_model,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return []


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Get embeddings for multiple texts in batch.
    Used during RAG document ingestion.
    """
    try:
        result = genai.embed_content(
            model=_embedding_model,
            content=texts,
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        return [[] for _ in texts]


async def classify_intent(query: str) -> dict:
    """
    Use Gemini or fast heuristics to classify user intent for the orchestrator.
    Returns: intent type and extracted entities (symbols, etc.)
    """
    import re
    cleaned = query.strip().lower()
    
    # 1. Fast heuristic matching for common prompts
    if re.match(r"^(h+e+y+|h+i+|h+e+l+o+|h+e+l+l+o+|howdy|yo|sup|good\s+(morning|afternoon|evening)|thanks?|thank\s+you|ok|okay|bye)$", cleaned):
        return {"intent": "greeting", "symbols": [], "confidence": 1.0}
        
    if "ipo" in cleaned or "gmp" in cleaned or "grey market" in cleaned:
        return {"intent": "ipo_info", "symbols": [], "confidence": 0.95}

    if "sip" in cleaned or "mutual fund" in cleaned or "systematic investment" in cleaned:
        return {"intent": "sip_advice", "symbols": [], "confidence": 0.95}

    if "market mood" in cleaned or "market sentiment" in cleaned or "bull" in cleaned and "bear" in cleaned:
        return {"intent": "market_sentiment", "symbols": [], "confidence": 0.95}

    # Detect paper trade commands
    if re.search(r"\b(buy|sell)\s+\d+\s+shares?\b", cleaned):
        symbol_match = re.search(r"\b(?:of\s+)?([A-Za-z0-9]+)\b", cleaned)
        symbols = [symbol_match.group(1).upper()] if symbol_match else []
        return {"intent": "paper_trade", "symbols": symbols, "confidence": 0.95}

    # Extract common Indian stock symbols from query
    known_symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
        "ITC", "KOTAKBANK", "LT", "HINDUNILVR", "TATAMOTORS", "BAJFINANCE", "MARUTI",
        "NIFTY", "SENSEX", "BANKNIFTY"
    ]
    detected_symbols = [s for s in known_symbols if s.lower() in cleaned.split() or f" {s.lower()} " in f" {cleaned} "]

    # 2. LLM Classification with Multi-Model Fallback
    classification_prompt = f"""
You are an intent classifier for a financial chatbot. 
Classify the user query into EXACTLY one of these intents:

  greeting       → casual hello, hi, hey, how are you, thanks
  stock_price    → asking for current price of a specific stock
  stock_analysis → asking for buy/sell signal, analysis, should I buy
  market_sentiment → asking about overall market mood, bulls/bears
  ipo_info       → asking about upcoming IPOs, GMP, grey market
  sip_advice     → asking about SIP, mutual funds, monthly investment
  paper_trade    → asking to buy/sell in virtual portfolio
  general_finance → any other finance question
  unknown        → completely unrelated to finance or markets

Return ONLY valid JSON, nothing else, no markdown:
{{
  "intent": "<one of the above>",
  "symbols": ["SYMBOL1", "SYMBOL2"],
  "confidence": 0.0-1.0
}}

Rules:
- "hi", "hello", "hey", "thanks", "how are you" = greeting ALWAYS
- Only extract symbols if they are explicitly named stocks/tickers
- If unsure, use general_finance not unknown
- NEVER return an intent not in the list above

User query: {query}
"""
    import json
    VALID_INTENTS = {
        "greeting", "stock_price", "stock_analysis", "market_sentiment",
        "ipo_info", "sip_advice", "paper_trade", "general_finance", "unknown"
    }

    for candidate in MODEL_CANDIDATES:
        try:
            model = get_chat_model(candidate)
            response = model.generate_content(classification_prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
                
            parsed = json.loads(text)
            if parsed.get("intent") not in VALID_INTENTS:
                parsed["intent"] = "general_finance"
            if not isinstance(parsed.get("symbols"), list):
                parsed["symbols"] = []
            if not parsed["symbols"] and detected_symbols:
                parsed["symbols"] = detected_symbols
                
            return parsed
        except Exception as e:
            logger.warning(f"Intent classification with {candidate} failed ({e}), trying next...")
            continue

    # Fallback to heuristic if all LLM candidates fail
    inferred_intent = "stock_analysis" if detected_symbols else "general_finance"
    return {
        "intent": inferred_intent,
        "symbols": detected_symbols,
        "timeframe": None,
        "action": None,
        "quantity": None,
        "risk_level": None,
    }
