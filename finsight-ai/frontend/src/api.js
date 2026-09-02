/**
 * FinSight AI — API Client
 */

import { supabase } from './lib/supabase';

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000'
).replace(/\/+$/, '');

const IS_DEV = import.meta.env.DEV;

console.log('[API] Backend:', API_BASE);


// ============================================================
// AUTH
// ============================================================

async function getAuthHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };

  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.access_token) {
      headers.Authorization =
        `Bearer ${session.access_token}`;
    } else if (IS_DEV) {
      headers.Authorization =
        'Bearer mock_jwt_token';
    }

    return headers;

  } catch (error) {

    console.error(
      '[API] Auth error:',
      error
    );

    if (IS_DEV) {
      headers.Authorization =
        'Bearer mock_jwt_token';
    }

    return headers;
  }
}


// ============================================================
// JSON REQUEST
// ============================================================

async function fetchJSON(
  endpoint,
  options = {}
) {
  const headers =
    await getAuthHeaders();

  let response;

  try {

    response = await fetch(
      `${API_BASE}${endpoint}`,
      {
        ...options,
        headers: {
          ...headers,
          ...(options.headers || {}),
        },
      }
    );

  } catch (error) {

    throw new Error(
      `Unable to connect to backend at ${API_BASE}`
    );
  }

  if (!response.ok) {

    let message =
      `API Error: ${response.status}`;

    try {

      const body =
        await response.json();

      message =
        body?.detail ||
        body?.message ||
        message;

    } catch {
      // Keep default.
    }

    throw new Error(message);
  }

  return response.json();
}


// ============================================================
// SSE
// ============================================================

function parseSSE(line) {

  const trimmed =
    String(line || '').trim();

  if (!trimmed.startsWith('data:')) {
    return null;
  }

  const jsonText =
    trimmed
      .replace(/^data:\s*/, '')
      .trim();

  if (!jsonText) {
    return null;
  }

  try {
    return JSON.parse(jsonText);
  } catch {
    console.warn(
      '[API] Invalid SSE JSON:',
      jsonText
    );
    return null;
  }
}


// ============================================================
// CHAT STREAM
// ============================================================

export async function* streamChat(
  message
) {

  if (!message?.trim()) {
    yield {
      type: 'error',
      content: 'Message cannot be empty.',
    };
    return;
  }

  let response;

  try {

    const authHeaders =
      await getAuthHeaders();

    response = await fetch(
      `${API_BASE}/api/chat`,
      {
        method: 'POST',
        headers: {
          ...authHeaders,
          Accept: 'text/event-stream',
        },
        body: JSON.stringify({
          message: message.trim(),
          stream: true,
        }),
      }
    );

  } catch (error) {

    yield {
      type: 'error',
      content:
        `Could not connect to server: ${error?.message ||
        'Failed to fetch'
        }`,
    };

    return;
  }

  if (!response.ok) {

    let detail =
      `${response.status} ${response.statusText}`;

    try {
      const data =
        await response.json();

      detail =
        data?.detail ||
        data?.message ||
        detail;

    } catch {
      // Keep detail.
    }

    yield {
      type: 'error',
      content: `Server error: ${detail}`,
    };

    return;
  }

  if (!response.body) {

    yield {
      type: 'error',
      content:
        'Server returned an empty response.',
    };

    return;
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let buffer = '';
  let terminal = false;

  try {

    while (true) {

      const {
        done,
        value,
      } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(
        value,
        { stream: true }
      );

      const lines =
        buffer.split('\n');

      buffer =
        lines.pop() || '';

      for (const line of lines) {

        const event =
          parseSSE(line);

        if (!event) {
          continue;
        }

        if (
          event.type === 'done' ||
          event.type === 'error'
        ) {
          terminal = true;
        }

        yield event;
      }
    }

    buffer += decoder.decode();

    if (buffer.trim()) {

      const event =
        parseSSE(buffer);

      if (event) {

        if (
          event.type === 'done' ||
          event.type === 'error'
        ) {
          terminal = true;
        }

        yield event;
      }
    }

    // Unexpected stream termination is an error,
    // not a successful completion.
    if (!terminal) {

      yield {
        type: 'error',
        content:
          'The server closed the stream unexpectedly.',
      };
    }

  } catch (error) {

    yield {
      type: 'error',
      content:
        `Stream terminated: ${error?.message ||
        'Unknown streaming error'
        }`,
    };

  } finally {

    try {
      await reader.cancel();
    } catch {
      // Already closed.
    }
  }
}


// ============================================================
// NORMAL CHAT
// ============================================================

export async function sendChat(
  message
) {
  return fetchJSON(
    '/api/chat',
    {
      method: 'POST',
      body: JSON.stringify({
        message,
        stream: false,
      }),
    }
  );
}


// ============================================================
// SIGNALS
// ============================================================

export async function getSignal(symbol) {
  return fetchJSON(
    `/api/signal/${encodeURIComponent(symbol)}`
  );
}

export async function getRecommendation(symbol) {
  return fetchJSON(
    `/api/signal/${encodeURIComponent(symbol)}/recommendation`
  );
}


// ============================================================
// IPO
// ============================================================

export async function getIPOs() {
  return fetchJSON('/api/ipo');
}

export async function getGMPData() {
  return fetchJSON('/api/ipo/gmp');
}


// ============================================================
// SIP
// ============================================================

export async function getSIPRecommendation(
  riskLevel,
  monthlyAmount,
  goalYears
) {
  return fetchJSON(
    '/api/sip',
    {
      method: 'POST',
      body: JSON.stringify({
        risk_level: riskLevel,
        monthly_amount: Number(
          monthlyAmount
        ),
        goal_years: Number(
          goalYears
        ),
      }),
    }
  );
}


// ============================================================
// PORTFOLIO
// ============================================================

export async function getPortfolio() {
  return fetchJSON('/api/portfolio');
}

export async function buyStock(
  symbol,
  quantity
) {
  return fetchJSON(
    '/api/portfolio/buy',
    {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        quantity: Number(quantity),
      }),
    }
  );
}

export async function sellStock(
  symbol,
  quantity
) {
  return fetchJSON(
    '/api/portfolio/sell',
    {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        quantity: Number(quantity),
      }),
    }
  );
}

export async function getTransactions(
  limit = 50
) {
  return fetchJSON(
    `/api/transactions?limit=${encodeURIComponent(limit)}`
  );
}

export async function resetPortfolio() {
  return fetchJSON(
    '/api/portfolio/reset',
    {
      method: 'POST',
      body: JSON.stringify({}),
    }
  );
}


// ============================================================
// MARKET
// ============================================================

export async function getStockData(
  symbol,
  period = '6mo'
) {
  return fetchJSON(
    `/api/stock/${encodeURIComponent(symbol)}?period=${encodeURIComponent(period)}`
  );
}

export async function getNifty50() {
  return fetchJSON(
    '/api/market/nifty50'
  );
}

export async function getMarketSentiment() {
  return fetchJSON(
    '/api/market/sentiment'
  );
}

export async function getNiftyHistory(
  period = '1d'
) {
  return fetchJSON(
    `/api/market/nifty50/history?period=${encodeURIComponent(period)}`
  );
}


// ============================================================
// SETTINGS
// ============================================================

export async function getSettings() {
  return fetchJSON('/api/user/settings');
}

export async function updateSettings(
  settings
) {
  return fetchJSON(
    '/api/user/settings',
    {
      method: 'PUT',
      body: JSON.stringify(settings),
    }
  );
}


// ============================================================
// RAG
// ============================================================

export async function ingestRAG(
  formData
) {

  const authHeaders =
    await getAuthHeaders();

  delete authHeaders['Content-Type'];

  const response =
    await fetch(
      `${API_BASE}/api/rag/ingest`,
      {
        method: 'POST',
        headers: authHeaders,
        body: formData,
      }
    );

  if (!response.ok) {

    let message =
      `API Error: ${response.status}`;

    try {
      const data =
        await response.json();

      message =
        data?.detail ||
        data?.message ||
        message;

    } catch {
      // Keep default.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function getRAGStats() {
  return fetchJSON('/api/rag/stats');
}


// ============================================================
// IPO ANALYSIS
// ============================================================

export async function analyzeIPO(
  ipoData
) {
  return fetchJSON(
    '/api/ipo/analyze',
    {
      method: 'POST',
      body: JSON.stringify(ipoData),
    }
  );
}