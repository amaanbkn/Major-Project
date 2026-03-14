/**
 * FinSight AI — API Client
 * Centralized API calls to the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function fetchJSON(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

// ── Chat ──────────────────────────────────────────────────
export async function* streamChat(message, userId = 'default') {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId, stream: true }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch (e) {
          // Skip malformed JSON
        }
      }
    }
  }
}

export async function sendChat(message, userId = 'default') {
  return fetchJSON('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, user_id: userId, stream: false }),
  });
}

// ── Signals ───────────────────────────────────────────────
export async function getSignal(symbol) {
  return fetchJSON(`/api/signal/${symbol}`);
}

export async function getRecommendation(symbol) {
  return fetchJSON(`/api/signal/${symbol}/recommendation`);
}

// ── IPO ───────────────────────────────────────────────────
export async function getIPOs() {
  return fetchJSON('/api/ipo');
}

export async function getGMPData() {
  return fetchJSON('/api/ipo/gmp');
}

// ── SIP ───────────────────────────────────────────────────
export async function getSIPRecommendation(riskLevel, monthlyAmount, goalYears) {
  return fetchJSON('/api/sip', {
    method: 'POST',
    body: JSON.stringify({
      risk_level: riskLevel,
      monthly_amount: monthlyAmount,
      goal_years: goalYears,
    }),
  });
}

// ── Portfolio ─────────────────────────────────────────────
export async function getPortfolio(userId = 'default') {
  return fetchJSON(`/api/portfolio?user_id=${userId}`);
}

export async function buyStock(symbol, quantity, userId = 'default') {
  return fetchJSON('/api/portfolio/buy', {
    method: 'POST',
    body: JSON.stringify({ symbol, quantity, user_id: userId }),
  });
}

export async function sellStock(symbol, quantity, userId = 'default') {
  return fetchJSON('/api/portfolio/sell', {
    method: 'POST',
    body: JSON.stringify({ symbol, quantity, user_id: userId }),
  });
}

export async function getTransactions(userId = 'default') {
  return fetchJSON(`/api/portfolio/transactions?user_id=${userId}`);
}

export async function resetPortfolio(userId = 'default') {
  return fetchJSON('/api/portfolio/reset', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

// ── Market Data ───────────────────────────────────────────
export async function getStockData(symbol, period = '6mo') {
  return fetchJSON(`/api/stock/${symbol}?period=${period}`);
}

export async function getNifty50() {
  return fetchJSON('/api/market/nifty50');
}

export async function getMarketSentiment() {
  return fetchJSON('/api/market/sentiment');
}
