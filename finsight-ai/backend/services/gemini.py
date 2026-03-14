"""
FinSight AI — Gemini Flash Client
Handles all interactions with Google Gemini 1.5 Flash:
  - Streaming text generation
  - Text embeddings (text-embedding-004)
  - System prompt construction
"""

import os
from typing import AsyncGenerator, Optional

import google.generativeai as genai
from loguru import logger

# ── Configure Gemini ─────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# ── Model instances (Singleton pattern) ─────────────────────
_chat_model = None
_embedding_model = "models/text-embedding-004"

SYSTEM_PROMPT = """You are FinSight AI, a sophisticated market research assistant built for the Indian stock market.

**Your capabilities:**
- Analyze live stock prices, technical indicators (RSI, Moving Averages), and market trends
- Provide weighted sentiment analysis from Economic Times, Moneycontrol, and Reddit
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


def get_chat_model():
    """Get or create the Gemini chat model (Singleton)."""
    global _chat_model
    if _chat_model is None:
        _chat_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_output_tokens=4096,
            ),
        )
        logger.info("✅ Gemini 1.5 Flash model initialized")
    return _chat_model


async def generate_response(prompt: str, context: str = "") -> str:
    """
    Generate a non-streaming response from Gemini.
    Used for internal tool calls and quick responses.
    """
    try:
        model = get_chat_model()
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        return f"I apologize, but I encountered an error processing your request: {str(e)}"


async def generate_streaming_response(
    prompt: str,
    context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response from Gemini.
    Yields text chunks as they arrive.
    """
    try:
        model = get_chat_model()
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = model.generate_content(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini streaming error: {e}")
        yield f"\n\n⚠️ Error: {str(e)}"


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
    Use Gemini to classify user intent for the orchestrator.
    Returns: intent type and extracted entities (symbols, etc.)
    """
    classification_prompt = f"""Analyze the following user query and classify it. Respond ONLY in this JSON format:
{{
    "intent": "<one of: stock_price, stock_analysis, market_sentiment, ipo_info, sip_advice, paper_trade, general_finance, greeting, unknown>",
    "symbols": ["<extracted stock symbols if any, e.g., RELIANCE, TCS>"],
    "timeframe": "<if mentioned: 1d, 1w, 1m, 3m, 6m, 1y, or null>",
    "action": "<if trade: BUY or SELL or null>",
    "quantity": <if mentioned: number or null>,
    "risk_level": "<if SIP: low, medium, high, or null>"
}}

User query: "{query}"
"""
    try:
        model = get_chat_model()
        response = model.generate_content(classification_prompt)
        # Parse the JSON response
        import json
        text = response.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {
            "intent": "general_finance",
            "symbols": [],
            "timeframe": None,
            "action": None,
            "quantity": None,
            "risk_level": None,
        }
