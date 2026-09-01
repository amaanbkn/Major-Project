/**
 * FinSight AI — API Client
 * Centralized API calls to the FastAPI backend.
 */

import { supabase } from './lib/supabase';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  const headers = { 'Content-Type': 'application/json' };
  // Use session token, or fall back to mock_jwt_token in dev mode (Supabase not configured)
  const token = session?.access_token || 'mock_jwt_token';
  headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function fetchJSON(url, options = {}) {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: { ...authHeaders, ...options.headers },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

// ── Chat ──────────────────────────────────────────────────
export async function* streamChat(message) {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({ message, stream: true }),
  });

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
  }

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
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

export async function sendChat(message) {
  return fetchJSON('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, stream: false }),
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
export async function getPortfolio() {
  return fetchJSON(`/api/portfolio`);
}

export async function buyStock(symbol, quantity) {
  return fetchJSON('/api/portfolio/buy', {
    method: 'POST',
    body: JSON.stringify({ symbol, quantity }),
  });
}

export async function sellStock(symbol, quantity) {
  return fetchJSON('/api/portfolio/sell', {
    method: 'POST',
    body: JSON.stringify({ symbol, quantity }),
  });
}

export async function getTransactions(limit = 50) {
  return fetchJSON(`/api/transactions?limit=${limit}`);
}

export async function resetPortfolio() {
  return fetchJSON('/api/portfolio/reset', {
    method: 'POST',
    body: JSON.stringify({}),
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

export async function getNiftyHistory(period = '1d') {
  return fetchJSON(`/api/market/nifty50/history?period=${period}`);
}

// ── Settings ──────────────────────────────────────────────
export async function getSettings() {
  return fetchJSON('/api/user/settings');
}

export async function updateSettings(settings) {
  return fetchJSON('/api/user/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

// ── RAG Ingestion ─────────────────────────────────────────
export async function ingestRAG(formData) {
  const authHeaders = await getAuthHeaders();
  const headers = { ...authHeaders };
  delete headers['Content-Type'];

  const response = await fetch(`${API_BASE}/api/rag/ingest`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

export async function getRAGStats() {
  return fetchJSON('/api/rag/stats');
}

// ── IPO Analysis ──────────────────────────────────────────
export async function analyzeIPO(ipoData) {
  return fetchJSON('/api/ipo/analyze', {
    method: 'POST',
    body: JSON.stringify(ipoData),
  });
}
