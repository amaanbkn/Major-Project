# FinSight AI 🚀

**LLM-Driven Financial Chatbot for Real-Time Stock Market Analysis**

> A Decoupled Three-Tier Multi-Agent RAG Framework for intelligent, accessible financial advisory — built as a VTU Final Year Capstone Project (2025-2026).

---

## 🎯 Problem Statement

With 130M+ SEBI-registered retail investors in India, there is a significant lack of intelligent, accessible advisory tools. FinSight AI bridges this gap using a Multi-Agent RAG architecture powered by Google Gemini.

## 🏗️ Architecture

```
┌─────────────────────┐      ┌──────────────────────────┐      ┌───────────────────┐
│   Presentation      │      │   Application Layer      │      │   Intelligence    │
│   React + Tailwind  │ ←──→ │   FastAPI + Orchestrator │ ←──→ │   Gemini Flash +  │
│   Recharts          │      │   APScheduler            │      │   ChromaDB RAG    │
│   (Vercel)          │      │   (Render)               │      │                   │
└─────────────────────┘      └──────────────────────────┘      └───────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │   Data Ingestion   │
                              │   yfinance • PRAW  │
                              │   RSS • BS4        │
                              └────────────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Stock Signals** | RSI + 50/200-day MA crossover → Buy/Hold/Sell signals |
| 💰 **SIP Advisor** | Risk-profiled fund recommendations with projections |
| 📋 **IPO Tracker** | BSE calendar + GMP from investorgain/chittorgarh |
| 📰 **Sentiment** | Weighted: ET RSS (40%) + Moneycontrol (40%) + Reddit (20%) |
| 💼 **Paper Trading** | ₹1,00,000 virtual balance, full P&L tracking |
| 🤖 **AI Chat** | Agentic orchestrator with real-time streaming |

## 🛠️ Tech Stack

- **Frontend:** React.js + TailwindCSS + Recharts
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
- Google Gemini API Key ([Get one free](https://aistudio.google.com/apikey))

### 1. Clone & Setup Environment
```bash
git clone <repo-url>
cd finsight-ai

# Copy environment template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
python main.py
```
Backend runs at `http://localhost:8000` • API docs at `/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

## 📁 Project Structure

```
finsight-ai/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, SQLite init
│   ├── agents/
│   │   ├── orchestrator.py            # Agentic coordinator
│   │   └── recommendation_engine.py   # Signal + Sentiment → Recommendation
│   ├── routers/
│   │   ├── chat.py                    # POST /api/chat (SSE streaming)
│   │   ├── signals.py                 # GET /api/signal/{symbol}
│   │   ├── ipo.py                     # GET /api/ipo
│   │   ├── sip.py                     # POST /api/sip
│   │   └── portfolio.py              # CRUD /api/portfolio
│   ├── services/
│   │   ├── market_data.py             # yfinance — live prices, NIFTY 50
│   │   ├── sentiment.py               # RSS + Reddit weighted sentiment
│   │   ├── ipo_tracker.py             # IPO + GMP scraper
│   │   ├── signals_engine.py          # RSI + MA crossover (pandas-ta)
│   │   ├── rag.py                     # ChromaDB RAG pipeline
│   │   ├── gemini.py                  # Gemini Flash client
│   │   └── scheduler.py              # APScheduler (30-min refresh)
│   ├── context_assembler.py           # Structured prompt builder
│   ├── trading_engine.py              # Paper trading (SQLite)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx               # Streaming chat with reasoning steps
│   │   │   ├── Dashboard.jsx          # Market overview + charts
│   │   │   ├── StockCard.jsx          # Signal analysis page
│   │   │   ├── IPOTracker.jsx         # IPO calendar + GMP
│   │   │   ├── SIPAdvisor.jsx         # Risk profiler + projections
│   │   │   └── Portfolio.jsx          # Paper trading interface
│   │   ├── api.js                     # API client + SSE helper
│   │   ├── App.jsx                    # Router + sidebar
│   │   └── main.jsx                   # Entry point
│   └── package.json
├── .env.example
└── README.md
```

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
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

### Backend → Render (Free Tier)
- Runtime: Python
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env vars: `GEMINI_API_KEY`, `FRONTEND_URL`

### Frontend → Vercel
- Framework: Vite
- Env var: `VITE_API_BASE_URL` → Render backend URL

## 👨‍💻 Team

| Name | USN | Role |
|------|-----|------|
| Amaan Siddiqui | 1DB23CS012 | Full-Stack Lead |
| Achuta Rao M | 1DB23CS004 | Backend & Data |
| Shreejal Dash | 1DB23CS201 | Frontend & UI |
| Kishan Kumar | 1DB23CS103 | ML & RAG Pipeline |

**Guide:** Mrs. Anjali Vyas, Dept of CSE, Don Bosco Institute of Technology, Bengaluru

## 📚 References

1. Luckianto et al. (2026) — Multi-Agent RAG for Financial Advisory
2. Liagkouras et al. (2025) — LSTM + Sentiment for Stock Prediction
3. Jadhav et al. (2025) — LLMs in Equity Markets

---

⚠️ **Disclaimer:** This is an academic project for educational and research purposes only. The information provided does not constitute financial advice. Always consult a SEBI-registered investment advisor before making investment decisions.
