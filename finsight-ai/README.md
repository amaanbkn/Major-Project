# FinSight AI

FinSight AI is a premium, LLM-driven financial research assistant and paper trading terminal tailored for the Indian stock market. It integrates live stock indices and technical signals, real-time news sentiment tracking, IPO calendars, a document-based RAG knowledge base, and SIP advisory tools into a unified platform.

## Architecture Overview

The system is split into two primary components: a React-based frontend application and a FastAPI-based backend server.

```
Frontend (React + Vite) 
     │
     ▼ (REST / SSE)
FastAPI Backend ────► SQLite (Virtual Portfolio & Trading Engine)
     │
     ├────► Supabase (Authentication JWT Validation)
     │
     ├────► ChromaDB Vector Store (RAG Document Retrieval)
     │
     └────► Google Gemini 1.5 Flash (Intent Routing & Financial Analysis)
```

1. **Frontend**: Built with React, TailwindCSS, and Vite. Fetches market prices, handles custom streaming chat components, virtual wallets, and manages RAG ingestion.
2. **FastAPI Backend**: Acts as the API gateway, orchestrating intelligence, executing paper trading operations on SQLite, validating authenticated users using Supabase JWT decoders, and fetching financial documentation contexts from ChromaDB.
3. **ChromaDB / RAG**: Stores chunked SEBI circulars, DRHP files, and RBI policies.
4. **Google Gemini 1.5 Flash**: Classifies user intents, parses trades, summarizes sentiment, and answers general financial queries.

---

## Prerequisites

- **Python** (version 3.10 or later)
- **Node.js** (version 18 or later) and **npm**
- **Git**
- Google Gemini API Key (Get one at [Google AI Studio](https://aistudio.google.com/apikey))
- Supabase Project URL and Anon Key (Configure a project at [supabase.com](https://supabase.com))

---

## Environment Setup

### 1. Backend Environment Setup

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Copy the `.env.example` template to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Populate the required keys in `backend/.env`:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `VITE_SUPABASE_URL`: Your Supabase URL.
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key.
   - `SUPABASE_JWT_SECRET`: Your Supabase project's JWT Secret (found in Supabase Settings -> API).

### 2. Frontend Environment Setup

1. Navigate to the `frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Copy the `.env.example` template to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Populate the required keys in `frontend/.env`:
   - `VITE_SUPABASE_URL`: Your Supabase URL (must match backend).
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key (must match backend).
   - `VITE_API_BASE_URL`: Set to `http://localhost:8000` for local development.

---

## How to Run Locally

### 1. Start the FastAPI Backend

1. Navigate to the `backend` directory (if not already there).
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the server using Uvicorn with auto-reload:
   ```bash
   uvicorn main:app --reload
   ```
   The backend API will be available at `http://localhost:8000`.

### 2. Start the React Frontend

1. Navigate to the `frontend` directory (if not already there).
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser and navigate to `http://localhost:5173`.

---

## Key Features

- **Personal AI Financial Chat**: Instantly routes natural language prompts to trade stocks, retrieve document excerpts, or calculate returns.
- **RAG Admin Control Panel**: Add new investment materials, PDFs, or circulars to the vector collection instantly.
- **Paper Trading Engine**: Track live gains and execute virtual buy/sell trades with a simulated ₹1,00,000 cash balance.
- **Unified Market Sentiment**: Fetches Economic Times and Moneycontrol news articles to build a composite market indicator.
