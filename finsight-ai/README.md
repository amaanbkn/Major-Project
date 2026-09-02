\# FinSight AI 🚀

**LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis**

A Decoupled Three-Tier Multi-Agent RAG Framework for intelligent, accessible financial advisory — built as a VTU Final Year Capstone Project (2025-2026).

## 🎯 Problem Statement

With 130M+ SEBI-registered retail investors in India, there is a significant lack of intelligent, accessible advisory tools. FinSight AI bridges this gap using a Multi-Agent RAG architecture powered by Google Gemini.

## 🏗️ Architecture

```
┌─────────────────────┐      ┌──────────────────────────┐      ┌───────────────────┐
│   Presentation      │      │   Application Layer      │      │   Intelligence    │
│   React + Tailwind  │ ←──→ │   FastAPI + Orchestrator │ ←──→ │   Gemini Flash +  │
│   Recharts (Vercel) │      │   APScheduler (Render)   │      │   ChromaDB RAG     │
└─────────────────────┘      └──────────────────────────┘      └───────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │   Data Ingestion   │
                              │  yfinance • PRAW    │
                              │  RSS • BeautifulSoup │
                              └────────────────────┘
```

## ✨ Features

| Feature | Description |
|---|---|
| 📊 Stock Signals | RSI + 50/200-day MA crossover → Buy/Hold/Sell signals |
| 💰 SIP Advisor | Risk-profiled fund recommendations with projections |
| 📋 IPO Tracker | BSE calendar + GMP from investorgain/chittorgarh |
| 📰 Sentiment | Weighted: ET RSS (40%) + Moneycontrol (40%) + Reddit (20%) |
| 💼 Paper Trading | ₹1,00,000 virtual balance, full P&L tracking |
| 🤖 AI Chat | Agentic orchestrator with real-time streaming |

## 🛠️ Tech Stack

- **Frontend:** React.js, TailwindCSS, Recharts
- **Backend:** FastAPI (Python, async)
- **LLM:** Google Gemini 1.5 Flash
- **Embeddings:** Gemini text-embedding-004
- **Vector DB:** ChromaDB
- **Database:** SQLite (dev) → Supabase (prod)
- **Scraping:** BeautifulSoup, PRAW, feedparser

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Google Gemini API Key](#) (free tier available)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd finsight-ai
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
python main.py
```
→ http://localhost:8000 (API docs at `/docs`)

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```
→ http://localhost:5173

## 📁 Project Structure

```
finsight-ai/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, SQLite init
│   ├── agents/
│   │   ├── orchestrator.py            # Agentic coordinator
│   │   └── recommendation_engine.py   # Signal + Sentiment → Recommendation
│   ├── routers/                       # chat, signals, ipo, sip, portfolio
│   ├── services/
│   │   ├── market_data.py             # yfinance — live prices, NIFTY 50
│   │   ├── sentiment.py               # RSS + Reddit weighted sentiment
│   │   ├── ipo_tracker.py             # IPO + GMP scraper
│   │   ├── signals_engine.py          # RSI + MA crossover (pandas-ta)
│   │   ├── rag.py                     # ChromaDB RAG pipeline
│   │   ├── gemini.py                  # Gemini Flash client
│   │   └── scheduler.py               # APScheduler (30-min refresh)
│   ├── context_assembler.py           # Structured prompt builder
│   ├── trading_engine.py              # Paper trading (SQLite)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                # Chat, Dashboard, StockCard, IPOTracker, SIPAdvisor, Portfolio
│   │   ├── api.js                     # API client + SSE helper
│   │   └── App.jsx                    # Router + sidebar
│   └── package.json
├── .env.example
└── README.md
```

## 🔑 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Chat with AI (SSE streaming) |
| GET | `/api/signal/{symbol}` | Technical analysis signal |
| GET | `/api/signal/{symbol}/recommendation` | Combined recommendation |
| GET | `/api/ipo` | IPO listings |
| GET | `/api/ipo/gmp` | Grey Market Premium |
| POST | `/api/sip` | SIP recommendation |
| GET | `/api/portfolio` | Get holdings |
| POST | `/api/portfolio/buy` | Paper buy |
| POST | `/api/portfolio/sell` | Paper sell |
| GET | `/api/portfolio/transactions` | Trade history |
| POST | `/api/portfolio/reset` | Reset to ₹1L |
| GET | `/api/stock/{symbol}` | Stock data + history |
| GET | `/api/market/nifty50` | NIFTY 50 snapshot |
| GET | `/api/market/sentiment` | Market sentiment |

## 🚢 Deployment

**Backend → Render (Free Tier)**
- Runtime: Python
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env vars: `GEMINI_API_KEY`, `FRONTEND_URL`

**Frontend → Vercel**
- Framework: Vite
- Env var: `VITE_API_BASE_URL` → Render backend URL

## 👨‍💻 Team

| Name | USN | Role |
|---|---|---|
| Amaan Siddiqui | 1DB23CS012 | Full-Stack Lead |
| Achuta Rao M | 1DB23CS004 | Backend & Data |
| Shreejal Dash | 1DB23CS201 | Frontend & UI |
| Kishan Kumar | 1DB23CS103 | ML & RAG Pipeline |



## 📚 References

- Luckianto et al. (2026) — Multi-Agent RAG for Financial Advisory
- Liagkouras et al. (2025) — LSTM + Sentiment for Stock Prediction
- Jadhav et al. (2025) — LLMs in Equity Markets

---

⚠️ **Disclaimer:** This is an academic project for educational and research purposes only. It does not constitute financial advice. Always consult a SEBI-registered investment advisor before making investment decisions.