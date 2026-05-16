"""
FinSight AI — Gemini Service Tests
Tests for intent classification and context assembly.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# Intent Classification Tests
# ═══════════════════════════════════════════════════════════════

class TestIntentClassification:
    """Test Gemini-based intent classification for various query types."""

    @pytest.mark.asyncio
    async def test_buy_shares_intent(self):
        """Queries like 'Buy 10 INFY shares' should classify as paper_trade."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "intent": "paper_trade",
            "symbols": ["INFY"],
            "confidence": 0.95,
        })

        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.return_value = mock_response

            from services.gemini import classify_intent
            result = await classify_intent("Buy 10 INFY shares")

            assert result["intent"] == "paper_trade"
            assert "INFY" in result["symbols"]
            assert result.get("confidence", 0) > 0

    @pytest.mark.asyncio
    async def test_portfolio_value_intent(self):
        """Queries about portfolio value should classify as paper_trade or general_finance."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "intent": "paper_trade",
            "symbols": [],
            "confidence": 0.85,
        })

        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.return_value = mock_response

            from services.gemini import classify_intent
            result = await classify_intent("What is my portfolio value?")

            assert result["intent"] in ("paper_trade", "general_finance")
            assert isinstance(result["symbols"], list)

    @pytest.mark.asyncio
    async def test_greeting_intent_shortcircuit(self):
        """Simple greetings like 'hi' should be classified directly without LLM call."""
        from services.gemini import classify_intent
        result = await classify_intent("hi")

        assert result["intent"] == "greeting"
        assert result["confidence"] == 1.0
        assert result["symbols"] == []

    @pytest.mark.asyncio
    async def test_stock_analysis_intent(self):
        """Queries like 'Should I buy RELIANCE?' should classify as stock_analysis."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "intent": "stock_analysis",
            "symbols": ["RELIANCE"],
            "confidence": 0.90,
        })

        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.return_value = mock_response

            from services.gemini import classify_intent
            result = await classify_intent("Should I buy RELIANCE?")

            assert result["intent"] == "stock_analysis"
            assert "RELIANCE" in result["symbols"]

    @pytest.mark.asyncio
    async def test_ipo_info_intent(self):
        """IPO-related queries should classify as ipo_info."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "intent": "ipo_info",
            "symbols": [],
            "confidence": 0.88,
        })

        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.return_value = mock_response

            from services.gemini import classify_intent
            result = await classify_intent("What are the upcoming IPOs?")

            assert result["intent"] == "ipo_info"

    @pytest.mark.asyncio
    async def test_invalid_intent_fallback(self):
        """If Gemini returns an invalid intent, it should fallback to general_finance."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "intent": "random_invalid_intent",
            "symbols": [],
            "confidence": 0.5,
        })

        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.return_value = mock_response

            from services.gemini import classify_intent
            result = await classify_intent("Tell me about SEBI regulations")

            assert result["intent"] == "general_finance"

    @pytest.mark.asyncio
    async def test_classification_error_fallback(self):
        """If Gemini call fails entirely, should return general_finance fallback."""
        with patch("services.gemini.get_chat_model") as mock_model:
            mock_model.return_value.generate_content.side_effect = Exception("API Error")

            from services.gemini import classify_intent
            result = await classify_intent("What is the NIFTY PE ratio?")

            assert result["intent"] == "general_finance"
            assert isinstance(result["symbols"], list)


# ═══════════════════════════════════════════════════════════════
# Context Assembly Tests
# ═══════════════════════════════════════════════════════════════

class TestContextAssembly:
    """Test the context_assembler module for proper prompt construction."""

    def test_basic_query_assembly(self):
        """Context should always contain the user query."""
        from context_assembler import assemble_context
        context = assemble_context(query="What is the price of TCS?")

        assert "[USER QUERY]" in context
        assert "What is the price of TCS?" in context
        assert "[TIMESTAMP]" in context

    def test_portfolio_data_in_context(self):
        """Portfolio data dict should be included in assembled context."""
        from context_assembler import assemble_context

        mock_portfolio = {
            "balance": 85000.50,
            "holdings": [
                {"symbol": "RELIANCE", "quantity": 10, "buy_price": 2800.00, "current_price": 2950.00},
                {"symbol": "TCS", "quantity": 5, "buy_price": 3900.00, "current_price": 4100.00},
            ],
        }

        context = assemble_context(
            query="Show my portfolio",
            portfolio_data=mock_portfolio,
        )

        assert "[PORTFOLIO]" in context
        assert "85000.5" in context or "85,000.5" in context or "85000.50" in context
        assert "[USER QUERY]" in context

    def test_market_data_in_context(self):
        """Market data should appear under [LIVE DATA] section."""
        from context_assembler import assemble_context

        mock_market = {
            "symbol": "INFY",
            "price": 1650.75,
            "change_pct": 1.2,
        }

        context = assemble_context(
            query="INFY price",
            market_data=mock_market,
        )

        assert "[LIVE DATA]" in context
        assert "INFY" in context
        assert "1650.75" in context

    def test_signal_data_in_context(self):
        """Signal data should appear under [SIGNALS] section."""
        from context_assembler import assemble_context

        mock_signal = {
            "symbol": "RELIANCE",
            "signal": "BUY",
            "signal_score": 2,
            "indicators": {
                "rsi": {"value": 45.2},
                "sma_50": 2800,
                "sma_200": 2650,
                "ma_crossover": "bullish",
            },
            "analysis": ["RSI neutral", "Price above 200 SMA"],
        }

        context = assemble_context(
            query="Analyse RELIANCE",
            signal_data=mock_signal,
        )

        assert "[SIGNALS]" in context
        assert "BUY" in context
        assert "RELIANCE" in context

    def test_sentiment_data_in_context(self):
        """Sentiment data should appear under [SENTIMENT] section."""
        from context_assembler import assemble_context

        mock_sentiment = {
            "overall_score": 0.35,
            "overall_label": "BULLISH",
            "sources": {
                "economic_times": {"score": 0.4, "weight": 0.4},
            },
        }

        context = assemble_context(
            query="Market mood",
            sentiment_data=mock_sentiment,
        )

        assert "[SENTIMENT]" in context
        assert "BULLISH" in context

    def test_reasoning_steps_in_context(self):
        """Reasoning steps should appear under [AGENT REASONING] section."""
        from context_assembler import assemble_context

        steps = ["Classified intent", "Fetched price", "Generated response"]
        context = assemble_context(
            query="hello",
            reasoning_steps=steps,
        )

        assert "[AGENT REASONING]" in context
        assert "Classified intent" in context
        assert "Step 1:" in context

    def test_ipo_data_in_context(self):
        """IPO data should appear under [IPO DATA] section."""
        from context_assembler import assemble_context

        mock_ipos = [
            {
                "name": "Bharti Hexacom",
                "price_band": "₹542 - ₹570",
                "gmp": "₹85",
                "open_date": "Apr 03, 2024",
                "close_date": "Apr 05, 2024",
            }
        ]

        context = assemble_context(
            query="Upcoming IPOs",
            ipo_data=mock_ipos,
        )

        assert "[IPO DATA]" in context
        assert "Bharti Hexacom" in context

    def test_empty_data_sections_excluded(self):
        """Sections with None data should not appear in context."""
        from context_assembler import assemble_context
        context = assemble_context(query="test query")

        assert "[LIVE DATA]" not in context
        assert "[SIGNALS]" not in context
        assert "[SENTIMENT]" not in context
        assert "[PORTFOLIO]" not in context
        assert "[IPO DATA]" not in context
        # But timestamp and query should always be present
        assert "[TIMESTAMP]" in context
        assert "[USER QUERY]" in context
