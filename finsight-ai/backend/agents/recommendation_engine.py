"""
FinSight AI — Recommendation Engine
Combines sentiment + technical → Buy/Hold/Sell with confidence score.
Also handles SIP recommendations based on risk profiling.
"""

from datetime import datetime
from typing import Optional

from loguru import logger


async def get_recommendation(
    symbol: str,
    signal_data: Optional[dict] = None,
    sentiment_data: Optional[dict] = None,
) -> dict:
    """
    Combine technical signals + sentiment to produce a final recommendation.

    Weighting:
    - Technical signal score: 60%
    - Sentiment score: 40%

    Returns: {symbol, recommendation, confidence, reasoning}
    """
    # Get signal data if not provided
    if signal_data is None:
        from services.signals_engine import compute_signals
        signal_data = await compute_signals(symbol)

    # Get sentiment if not provided
    if sentiment_data is None:
        from services.sentiment import get_market_sentiment
        sentiment_data = await get_market_sentiment()

    # Extract scores
    tech_score = signal_data.get("signal_score", 0) / 3  # Normalize to -1 to 1
    sent_score = sentiment_data.get("overall_score", 0)  # Already -1 to 1

    # Weighted composite
    composite = (tech_score * 0.60) + (sent_score * 0.40)
    confidence = min(abs(composite) * 100, 95)  # Cap at 95%

    # Determine recommendation
    if composite > 0.3:
        recommendation = "STRONG_BUY"
    elif composite > 0.1:
        recommendation = "BUY"
    elif composite < -0.3:
        recommendation = "STRONG_SELL"
    elif composite < -0.1:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    reasoning = []
    reasoning.append(f"Technical signal: {signal_data.get('signal', 'N/A')} (score: {signal_data.get('signal_score', 0)}/3)")
    reasoning.append(f"Market sentiment: {sentiment_data.get('overall_label', 'N/A')} ({sentiment_data.get('overall_score', 0)})")
    reasoning.append(f"Composite score: {round(composite, 3)} (Tech 60% + Sentiment 40%)")
    reasoning.append(f"Confidence: {round(confidence, 1)}%")

    return {
        "symbol": symbol.upper(),
        "recommendation": recommendation,
        "composite_score": round(composite, 3),
        "confidence": round(confidence, 1),
        "technical": {
            "signal": signal_data.get("signal", "N/A"),
            "score": signal_data.get("signal_score", 0),
            "weight": 0.60,
        },
        "sentiment": {
            "label": sentiment_data.get("overall_label", "N/A"),
            "score": sentiment_data.get("overall_score", 0),
            "weight": 0.40,
        },
        "reasoning": reasoning,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": (
            "This is an AI-generated analysis for educational purposes only. "
            "Not financial advice. Consult a SEBI-registered advisor before investing."
        ),
    }


def get_sip_recommendation(
    risk_level: str,
    monthly_amount: float,
    goal_years: int,
) -> dict:
    """
    SIP recommendation based on risk appetite.

    Risk levels:
    - low: Debt funds + large-cap (70:30)
    - medium: Large-cap + Mid-cap + Debt (40:30:30)
    - high: Mid-cap + Small-cap + Large-cap (40:35:25)
    """
    risk_level = risk_level.lower().strip()

    # Expected annual returns (historical average)
    returns_map = {
        "low": 0.08,       # 8% p.a.
        "medium": 0.12,    # 12% p.a.
        "high": 0.15,      # 15% p.a.
    }

    # Fund allocation
    allocation_map = {
        "low": [
            {"type": "Debt Fund", "allocation": 70, "example": "HDFC Corporate Bond Fund / ICICI Pru All Seasons Bond"},
            {"type": "Large Cap Fund", "allocation": 30, "example": "SBI Bluechip Fund / Mirae Asset Large Cap Fund"},
        ],
        "medium": [
            {"type": "Large Cap Fund", "allocation": 40, "example": "Mirae Asset Large Cap / Canara Robeco Bluechip"},
            {"type": "Mid Cap Fund", "allocation": 30, "example": "HDFC Mid-Cap Opportunities / Kotak Emerging Equity"},
            {"type": "Debt Fund", "allocation": 30, "example": "HDFC Short Term Debt / Axis Banking & PSU Debt"},
        ],
        "high": [
            {"type": "Mid Cap Fund", "allocation": 40, "example": "Quant Mid Cap / PGIM India Midcap Opportunities"},
            {"type": "Small Cap Fund", "allocation": 35, "example": "Quant Small Cap / Nippon India Small Cap"},
            {"type": "Large Cap Fund", "allocation": 25, "example": "Mirae Asset Large Cap / UTI Nifty 50 Index Fund"},
        ],
    }

    if risk_level not in allocation_map:
        risk_level = "medium"

    annual_return = returns_map[risk_level]
    monthly_return = annual_return / 12
    months = goal_years * 12

    # SIP Future Value = P × [(1+r)^n - 1] / r × (1+r)
    if monthly_return > 0:
        future_value = monthly_amount * (
            ((1 + monthly_return) ** months - 1) / monthly_return
        ) * (1 + monthly_return)
    else:
        future_value = monthly_amount * months

    total_invested = monthly_amount * months
    estimated_returns = future_value - total_invested

    allocations = []
    for fund in allocation_map[risk_level]:
        fund_amount = monthly_amount * (fund["allocation"] / 100)
        allocations.append({
            **fund,
            "monthly_amount": round(fund_amount, 2),
        })

    return {
        "risk_level": risk_level,
        "monthly_amount": monthly_amount,
        "goal_years": goal_years,
        "expected_annual_return": f"{annual_return * 100:.0f}%",
        "projections": {
            "total_invested": round(total_invested, 2),
            "estimated_value": round(future_value, 2),
            "estimated_returns": round(estimated_returns, 2),
            "wealth_created_multiplier": round(future_value / total_invested, 2),
        },
        "recommended_allocation": allocations,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": (
            "Past performance is not indicative of future results. "
            "These are estimates based on historical average returns. "
            "Consult a SEBI-registered advisor for personalized advice."
        ),
    }
