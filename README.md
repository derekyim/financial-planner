# Dysprosium Financial Assistant

AI-Powered Financial Planning & Analysis for Ecommerce Businesses.

A multi-agent system built on LangGraph that connects to Google Sheets financial models via API, enabling FP&A analysts to ask natural-language questions about their financial data, run goal-seek optimizations, and get strategic business guidance through RAG-powered knowledge retrieval.

## Architecture

```
Next.js/React UI  -->  FastAPI Backend  -->  LangGraph Supervisor
                                                  |
                            ┌─────────────┬───────┴──────┬──────────┐
                          Recall     Goal Seek     Strategic     Respond
                            |            |             |
                       GSheets API  GSheets API   RAG + Tavily
```

**Agents:**
- **Recall** — Reads model facts, metrics, and formula chains from Google Sheets
- **Goal Seek** — Finds optimal input values to hit target KPIs using scenario analysis
- **Strategic Guidance** — RAG over business knowledge base + Tavily web search for current trends
- **Respond** — Direct answers for simple queries

**Key Technologies:** LangGraph, LangChain, OpenAI (GPT-4o / GPT-4o-mini), Qdrant, RAGAS, Tavily, gspread, Next.js, Material UI

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud service account with Sheets API access
- API keys for OpenAI, Tavily, and (optionally) LangSmith

## Setup

### 1. Environment Variables

Create a `.env` file in `backend/`:

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
GOOGLE_CREDENTIALS_PATH=credentials.json
SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit
LANGCHAIN_API_KEY=lsv2-...        # optional, for LangSmith tracing
LANGCHAIN_TRACING_V2=true          # optional
ADVANCED_RETRIEVAL=false           # set to true for hybrid BM25+dense retrieval
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
python -m api.index
```

The API server starts at `http://localhost:8000`.

### 3. Frontend

```bash
cd ui
npm install
npm run dev
```

The UI opens at `http://localhost:3000`.

## Running Tests

```bash
cd backend

# Unit tests (mocked, no API keys needed)
.venv/bin/python -m pytest tests/ -v

# Integration tests (requires credentials + live Google Sheet)
.venv/bin/python -m pytest integration_tests/ -v -m integration
```

## Running Evaluations

```bash
cd backend

# Run all evals (RAG + Agent)
.venv/bin/python -m evals.run_evals --all

# RAG evals only
.venv/bin/python -m evals.run_evals --rag

# Agent evals only
.venv/bin/python -m evals.run_evals --agent
```

### A/B Evaluation (Baseline vs. Hybrid Retrieval)

```bash
# Baseline (dense-only retrieval)
ADVANCED_RETRIEVAL=false .venv/bin/python -m evals.run_evals --rag

# Improved (hybrid BM25 + dense with Reciprocal Rank Fusion)
ADVANCED_RETRIEVAL=true .venv/bin/python -m evals.run_evals --rag
```

## Project Structure

```
backend/
  agents/           # LangGraph agent definitions and tools
    financial_agent.py   # Main multi-agent graph
    rag_pipeline.py      # RAG pipeline (dense + hybrid retrieval)
    playbooks.py         # Agent system prompts
    tools.py             # Google Sheets tools
    strategic_tools.py   # Tavily web search tool
    memory_types.py      # 5 memory types
  evals/             # RAGAS evaluation framework
  shared/            # Shared utilities and evaluations
  test_data/         # Manual test cases for evaluation
  tests/             # Unit tests
  integration_tests/ # Integration tests (live APIs)
  data/              # Knowledge base documents for RAG
  api/               # FastAPI server
  docs/              # Project documentation

ui/
  pages/             # Next.js pages (chat, docs, evals)
  components/        # React components (ChatMessage, DebugPane, ModelPicker)
  services/          # Chat service, tour engine, session store
```
