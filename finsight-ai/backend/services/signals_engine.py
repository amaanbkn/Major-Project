"""
FinSight AI — Technical Signals Engine
RSI + 50/200-day Moving Average Crossover using pandas-ta.
Generates Buy / Hold / Sell signals.
"""

import asyncio
from datetime import datetime
from typing import Optional

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from loguru import logger


def _nse_symbol(symbol: str) -> str:
    """Convert plain symbol to NSE Yahoo Finance ticker."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    return symbol


async def compute_signals(symbol: str) -> dict:
    """
    Compute technical signals for a given stock:
    - RSI (14-period)
    - SMA 50 (50-day simple moving average)
    - SMA 200 (200-day simple moving average)
    - Golden Cross / Death Cross detection
    - Overall signal: BUY / HOLD / SELL

    Returns a comprehensive signal dictionary.
    """
    try:
        ticker = yf.Ticker(_nse_symbol(symbol))
        df: pd.DataFrame = await asyncio.to_thread(
            lambda: ticker.history(period="1y", interval="1d")
        )

        if df.empty or len(df) < 50:
            return {
                "symbol": symbol.upper(),
                "signal": "INSUFFICIENT_DATA",
                "message": f"Not enough historical data for {symbol}. Need at least 50 trading days.",
                "status": "error",
            }

        # ── Calculate indicators ─────────────────────────────
        # RSI (14-period)
        df["RSI"] = ta.rsi(df["Close"], length=14)

        # Simple Moving Averages
        df["SMA_50"] = ta.sma(df["Close"], length=50)
        df["SMA_200"] = ta.sma(df["Close"], length=200) if len(df) >= 200 else None

        # EMA for additional context
        df["EMA_20"] = ta.ema(df["Close"], length=20)

        # MACD
        macd = ta.macd(df["Close"])
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

        # Bollinger Bands
        bbands = ta.bbands(df["Close"], length=20)
        if bbands is not None:
            df = pd.concat([df, bbands], axis=1)

        # ── Extract latest values ────────────────────────────
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        current_price = round(float(latest["Close"]), 2)
        rsi = round(float(latest["RSI"]), 2) if pd.notna(latest["RSI"]) else None
        sma_50 = round(float(latest["SMA_50"]), 2) if pd.notna(latest["SMA_50"]) else None
        sma_200 = round(float(latest.get("SMA_200", float("nan"))), 2) if pd.notna(latest.get("SMA_200")) else None
        ema_20 = round(float(latest["EMA_20"]), 2) if pd.notna(latest["EMA_20"]) else None

        # ── Signal Logic ─────────────────────────────────────
        signals = []
        signal_score = 0  # -3 to +3 score for final signal

        # RSI Analysis
        rsi_signal = "NEUTRAL"
        if rsi is not None:
            if rsi < 30:
                rsi_signal = "OVERSOLD"
                signal_score += 1
                signals.append(f"RSI ({rsi}) indicates oversold — potential buying opportunity")
            elif rsi > 70:
                rsi_signal = "OVERBOUGHT"
                signal_score -= 1
                signals.append(f"RSI ({rsi}) indicates overbought — consider taking profits")
            else:
                signals.append(f"RSI ({rsi}) is in neutral zone")

        # Moving Average Crossover
        ma_signal = "NEUTRAL"
        if sma_50 is not None and sma_200 is not None:
            prev_sma_50 = float(prev["SMA_50"]) if pd.notna(prev["SMA_50"]) else None
            prev_sma_200 = float(prev.get("SMA_200", float("nan"))) if pd.notna(prev.get("SMA_200")) else None

            if prev_sma_50 and prev_sma_200:
                # Golden Cross: SMA50 crosses above SMA200
                if prev_sma_50 <= prev_sma_200 and sma_50 > sma_200:
                    ma_signal = "GOLDEN_CROSS"
                    signal_score += 2
                    signals.append("🟢 Golden Cross detected (SMA50 crossed above SMA200) — Strong BUY signal")
                # Death Cross: SMA50 crosses below SMA200
                elif prev_sma_50 >= prev_sma_200 and sma_50 < sma_200:
                    ma_signal = "DEATH_CROSS"
                    signal_score -= 2
                    signals.append("🔴 Death Cross detected (SMA50 crossed below SMA200) — Strong SELL signal")
                elif sma_50 > sma_200:
                    ma_signal = "BULLISH"
                    signal_score += 1
                    signals.append(f"SMA50 ({sma_50}) above SMA200 ({sma_200}) — Bullish trend")
                else:
                    ma_signal = "BEARISH"
                    signal_score -= 1
                    signals.append(f"SMA50 ({sma_50}) below SMA200 ({sma_200}) — Bearish trend")
        elif sma_50 is not None:
            if current_price > sma_50:
                signal_score += 0.5
                signals.append(f"Price ({current_price}) above SMA50 ({sma_50}) — Short-term bullish")
            else:
                signal_score -= 0.5
                signals.append(f"Price ({current_price}) below SMA50 ({sma_50}) — Short-term bearish")

        # Price vs EMA20
        if ema_20 is not None:
            if current_price > ema_20:
                signals.append(f"Price above EMA20 ({ema_20}) — Positive momentum")
            else:
                signals.append(f"Price below EMA20 ({ema_20}) — Weakening momentum")

        # ── Overall Signal ───────────────────────────────────
        if signal_score >= 2:
            overall_signal = "STRONG_BUY"
        elif signal_score >= 1:
            overall_signal = "BUY"
        elif signal_score <= -2:
            overall_signal = "STRONG_SELL"
        elif signal_score <= -1:
            overall_signal = "SELL"
        else:
            overall_signal = "HOLD"

        return {
            "symbol": symbol.upper(),
            "signal": overall_signal,
            "signal_score": round(signal_score, 1),
            "current_price": current_price,
            "indicators": {
                "rsi": {"value": rsi, "signal": rsi_signal},
                "sma_50": sma_50,
                "sma_200": sma_200,
                "ema_20": ema_20,
                "ma_crossover": ma_signal,
            },
            "analysis": signals,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Signal computation error for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "signal": "ERROR",
            "error": str(e),
            "status": "error",
        }


async def get_signal_summary(symbol: str) -> str:
    """Get a human-readable signal summary for the context assembler."""
    result = await compute_signals(symbol)
    if result["status"] != "success":
        return f"Signal data unavailable for {symbol}: {result.get('error', 'Unknown error')}"

    lines = [
        f"**{symbol} Technical Signal: {result['signal']}** (Score: {result['signal_score']}/3)",
        f"Current Price: ₹{result['current_price']}",
    ]

    indicators = result["indicators"]
    if indicators["rsi"]["value"]:
        lines.append(f"RSI(14): {indicators['rsi']['value']} ({indicators['rsi']['signal']})")
    if indicators["sma_50"]:
        lines.append(f"SMA 50: ₹{indicators['sma_50']}")
    if indicators["sma_200"]:
        lines.append(f"SMA 200: ₹{indicators['sma_200']}")
    lines.append(f"MA Crossover: {indicators['ma_crossover']}")

    for analysis in result.get("analysis", []):
        lines.append(f"  • {analysis}")

    return "\n".join(lines)
