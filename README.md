<div align="center">

# <span style="color:#4285F4">N</span><span style="color:#EA4335">o</span><span style="color:#FBBC05">t</span><span style="color:#4285F4">G</span><span style="color:#34A853">o</span><span style="color:#EA4335">o</span><span style="color:#4285F4">g</span><span style="color:#34A853">l</span><span style="color:#EA4335">e</span>

**Privacy-Preserving, AI-Augmented Hybrid Search Engine & Autonomous Web Crawler**

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%7C%20pgvector-336791.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-SearXNG-2496ED.svg?logo=docker&logoColor=white)](https://docs.searxng.org/)
[![LiteLLM](https://img.shields.io/badge/LLM-LiteLLM%20%2F%20Gemini-orange.svg)](https://litellm.ai/)

<p align="center">
  A full-stack, production-grade search engine combining <b>Zero-Knowledge Privacy Sanitization</b>, <b>BM25 Lexical + pgvector Semantic Retrieval (RRF)</b>, <b>Cross-Encoder Neural Reranking</b>, <b>LiteLLM AI Overviews (SGE)</b>, and an <b>Autonomous 24/7 Web Crawler</b> with seamless persistence and resume.
</p>

[Quickstart](#-quickstart-guide) • [Architecture](#-architecture--data-flow) • [Features](#-key-features) • [API Reference](#-api-reference) • [Crawler & Persistence](#-autonomous-crawler--resumption)

</div>

---

## 🌟 Key Features

### 🛡️ Zero-Knowledge Privacy Boundary
- **PII Detection & Redaction**: Automatically scans queries for sensitive data before external dispatch — emails, phone numbers, IPv4/IPv6 addresses, API keys (`sk-...`), and passwords.
- **Query Minimization**: Strips conversational fluff and personal identifiable context while retaining precise semantic intent.
- **Audit-Safe & Ephemeral**: Sensitive tokens never enter database logs, LLM context windows, or external search providers.

### ⚡ Hybrid Search & Neural Reranking Pipeline
- **BM25 Lexical Search**: Custom inverted index with stemming, token frequency scoring, and stopword filtering for high keyword precision.
- **Dense Vector Search (`pgvector`)**: 384-dimensional dense semantic vectors using `all-MiniLM-L6-v2` with HNSW cosine distance indexing for semantic understanding.
- **Reciprocal Rank Fusion (RRF)**: Merges sparse BM25 scores with dense vector ranks using tunable constant $k=60$.
- **Cross-Encoder Neural Reranker**: Employs `ms-marco-MiniLM-L-6-v2` to score joint `(query, document)` pairs with full cross-attention and Sigmoid normalization.

### 🤖 Interactive AI Overview (SGE)
- **Factual LLM Summaries**: Powered by LiteLLM (configurable with Google Gemini 2.5 Flash, Groq Llama 3.3, OpenAI GPT-4o, or local Ollama).
- **Verifiable Inline Citations**: Context grounded with numbered citation tags (`[1]`, `[2]`) linking directly to interactive source chips.
- **Privacy Scrubbing**: Prompt context is automatically scrubbed of sensitive information before reaching the LLM.

### 🕷️ Continuous Autonomous Web Crawler
- **24/7 Background Crawler**: Asynchronously discovers, fetches, and parses web pages with politeness delays and per-domain throttling.
- **Smart Deduplication**: Dual-stage filter using SHA-256 for exact matches and 64-bit SimHash (Hamming distance) for near-duplicate content.
- **Real-Time Query Ingestion**: When users perform searches, newly discovered web results from SearXNG are immediately queued into the frontier and indexed into PostgreSQL and BM25 on the fly.
- **Persistence & Resume**: If the backend stops, visited URLs and discovered outlinks are preserved in PostgreSQL. On restart, the crawler automatically restores its frontier without re-crawling visited pages.

### 🎨 Authentic Google-Inspired Frontend ("NotGoogle")
- **Google Design Fidelity**: Pixel-accurate Google search interface featuring the iconic multi-colored wordmark, Light/Dark mode toggle, search filter tabs, and "NotGooooogle" pagination.
- **Interactive Crawler HUD**: Live crawler status badge in the header polling `/crawler/status`, with a full modal showing indexed document counts, frontier queue size, and an instant keyword/URL seeder.
- **Rich Result Cards & Sidebar**: Domain breadcrumbs, cached snippets, SearXNG knowledge panel, and quick query actions.

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart TD
    User([User Query]) --> Privacy[🛡️ Privacy Guard<br/>PII Detector & Minimizer]
    Privacy --> CleanQuery[Sanitized Query]

    subgraph Retrieval["Hybrid Retrieval & Reranking"]
        CleanQuery --> BM25[BM25 Inverted Index<br/>Keyword Search]
        CleanQuery --> Vector[pgvector HNSW<br/>all-MiniLM-L6-v2]
        BM25 --> RRF[Reciprocal Rank Fusion<br/>RRF k=60]
        Vector --> RRF
        RRF --> Rerank[Cross-Encoder Reranker<br/>ms-marco-MiniLM-L-6-v2]
    end

    subgraph WebDiscovery["Live Web Aggregation & Ingestion"]
        CleanQuery --> SearXNG[SearXNG Meta-Search<br/>Local Docker Service]
        SearXNG --> WebResults[Live Web Results]
        WebResults -. Top URLs .-> RealtimeIngest[Immediate Crawler Ingest]
        WebResults -. Outlinks .-> Frontier[(URL Frontier Queue)]
    end

    subgraph Crawler["24/7 Autonomous Crawler Engine"]
        Frontier --> Fetcher[Async HTTP Fetcher<br/>httpx + Politeness]
        Fetcher --> Extractor[HTML Extractor<br/>BeautifulSoup4]
        Extractor --> Dedup{SimHash & SHA-256<br/>Deduplicator}
        Dedup -- Unique --> DB[(PostgreSQL Cloud / Local<br/>pgvector Store)]
        Dedup -- Unique --> Indexer[BM25 Pickle Index<br/>search_index.pkl]
        Extractor -. Discovered Outlinks .-> Frontier
    end

    RealtimeIngest --> DB
    RealtimeIngest --> Indexer

    Rerank --> Synthesizer[Result Synthesizer<br/>Merge Local & Web Results]
    WebResults --> Synthesizer

    Synthesizer --> Overview[AI Overview Generator<br/>LiteLLM / Gemini 2.5]
    Synthesizer --> Frontend[React 19 UI<br/>Google-authentic Presentation]
    Overview --> Frontend
```

---

## 📁 Repository Structure

```
NotGoogle/
├── NotGoogle/                       # Python Backend (FastAPI, Search Engines, Crawler)
│   ├── app/
│   │   ├── api/
│   │   │   ├── main.py              # FastAPI app, lifespan, /search, /crawler routes
│   │   │   └── schemas.py           # Pydantic schemas (SearchResponse, Document, etc.)
│   │   ├── engine/
│   │   │   ├── bm25.py              # BM25 ranking algorithm implementation
│   │   │   ├── indexer.py           # Inverted index with pickle serialization
│   │   │   ├── vector_store.py      # pgvector storage & sentence-transformers embeddings
│   │   │   ├── hybrid.py            # Reciprocal Rank Fusion (RRF) combiner
│   │   │   ├── reranker.py          # Cross-encoder (ms-marco-MiniLM-L-6-v2)
│   │   │   ├── searxng.py           # SearXNG metasearch client integration
│   │   │   ├── overview.py          # LiteLLM AI Overview generator with citations
│   │   │   ├── evidence.py          # Evidence compiler & snippet formatter
│   │   │   └── crawler/
│   │   │       ├── pipeline.py      # Continuous background crawler & indexer
│   │   │       ├── frontier.py      # Politeness-aware URL frontier & FIFO queue
│   │   │       ├── extractor.py     # HTML text, title, and link extraction
│   │   │       ├── dedup.py         # 64-bit SimHash and SHA-256 content deduplication
│   │   │       └── storage.py       # PostgreSQL asyncpg document storage & schema
│   │   ├── privacy/
│   │   │   ├── detector.py          # Regex & semantic PII pattern detector
│   │   │   ├── minimizer.py         # Query minimization and fluff remover
│   │   │   └── service.py           # Privacy service orchestrator & sanitizer
│   │   └── query/
│   │       └── processor.py         # Query normalization, tokenizer, and filter
│   ├── docker-compose.yaml          # SearXNG, PostgreSQL, and RabbitMQ containers
│   ├── searxng/                     # SearXNG local configuration
│   ├── test_privacy.py              # Unit tests for the Privacy Engine
│   ├── requirements.txt             # Python dependencies
│   ├── search_index.pkl             # Persisted BM25 inverted index state
│   ├── .env.example                 # Backend environment variable template
│   └── .env                         # Local runtime environment variables
│
└── frontend/                        # Frontend Application (React 19 + Vite + Tailwind)
    ├── src/
    │   ├── App.jsx                  # Main NotGoogle UI, search state, modals, tabs
    │   ├── App.css                  # Custom styling & animations
    │   ├── index.css                # Tailwind directives & typography
    │   └── main.jsx                 # Application entry point
    ├── package.json                 # Node dependencies (React 19, Lucide, Tailwind)
    ├── vite.config.js               # Vite development configuration
    └── tailwind.config.js           # Tailwind theme configuration
```

---

### ⚡ One-Click Startup (Recommended)
You can launch the entire stack (Docker SearXNG + FastAPI Backend + React Vite Frontend) with a single command from the project root:

```bash
# Start everything:
./start.sh
```

To stop all services cleanly anytime, press `Ctrl+C` in that terminal or run:
```bash
./stop.sh
```

---

### Manual Step-by-Step Setup

If you prefer starting each service individually:

#### Step 1: Clone and Configure Environment

```bash
# Clone the repository
git clone https://github.com/your-username/NotGoogle.git
cd NotGoogle
```

Configure backend environment variables:
```bash
cd NotGoogle
cp .env.example .env
```

Edit `.env` with your preferred configuration:
```env
# Database connection (Local PostgreSQL or Neon Cloud PostgreSQL)
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/notgoogle

# SearXNG URL (default Docker port)
SEARXNG_URL=http://localhost:8080

# AI Overview Model (LiteLLM syntax)
LLM_MODEL=gemini/gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### Step 2: Start Supporting Services (Docker)

Launch SearXNG (and optional local PostgreSQL/RabbitMQ):
```bash
# From within the NotGoogle/ backend directory:
docker compose up -d searxng
```

Verify SearXNG is running by opening:
[http://localhost:8080](http://localhost:8080)

---

### Step 3: Set Up and Start Backend

```bash
cd NotGoogle

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI backend server
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend server will automatically:
1. Connect to PostgreSQL and initialize tables (`documents`).
2. Load the BM25 inverted index from `search_index.pkl`.
3. Initialize the `all-MiniLM-L6-v2` dense embedding model and `ms-marco-MiniLM-L-6-v2` Cross-Encoder.
4. Restore unvisited outlinks from PostgreSQL into the URL frontier.
5. Launch the autonomous background crawler.

Verify backend health:
```bash
curl http://localhost:8000/health
```

---

### Step 4: Set Up and Start Frontend

In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at:
**[http://localhost:5173](http://localhost:5173)**

You will be greeted by the authentic **NotGoogle** home view!

---

## 🔌 API Reference

### 1. Unified Search (`GET /search`)
Executes the privacy boundary, hybrid retrieval, neural reranking, live web discovery, and optional AI Overview synthesis.

```http
GET /search?q={query}&limit=10&offset=0&ai_overview=true&include_searxng=true
```

| Parameter | Type | Default | Description |
|:---|:---|:---|:---|
| `q` | `string` | *(Required)* | The user query (sanitized before downstream processing) |
| `limit` | `int` | `10` | Number of results to return per page (1 to 50) |
| `offset` | `int` | `0` | Pagination offset |
| `ai_overview` | `bool` | `false` | When `true`, synthesizes a cited AI Overview using LiteLLM |
| `include_searxng` | `bool` | `true` | Includes live multi-engine web aggregation |

#### Example Response:
```json
{
  "query": "fastapi tutorial",
  "total_res": 15,
  "ai_overview": {
    "summary": "FastAPI is a modern, high-performance web framework for Python based on standard type hints [1]. It features automatic OpenAPI docs and high execution speed [2].",
    "sources": [
      { "index": 1, "title": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com" },
      { "index": 2, "title": "Python Official Documentation", "url": "https://docs.python.org" }
    ],
    "model_used": "gemini/gemini-2.5-flash"
  },
  "resp": [
    {
      "id": "1",
      "title": "FastAPI Tutorial - First Steps",
      "url": "https://fastapi.tiangolo.com/tutorial/first-steps/",
      "snippet": "Creating a first FastAPI application step-by-step with automatic API docs...",
      "score": 0.9421,
      "source": "cross_encoder"
    }
  ],
  "searxng_resp": [...]
}
```

---

### 2. Live Crawler Management

#### `GET /crawler/status`
Returns live statistics about the continuous crawler.
```json
{
  "is_running": true,
  "pages_crawled": 418,
  "pages_indexed": 418,
  "queue_size": 16420,
  "duplicates_skipped": 73,
  "errors_count": 5
}
```

#### `POST /crawler/seed`
Injects starting URLs or discovers seeds via keywords using SearXNG.
```json
{
  "urls": ["https://en.wikipedia.org/wiki/Information_retrieval"],
  "keywords": ["distributed systems", "vector databases"]
}
```

#### `POST /crawler/start` & `POST /crawler/stop`
Starts or halts the continuous background crawler task.
```bash
curl -X POST http://localhost:8000/crawler/start
curl -X POST http://localhost:8000/crawler/stop
```

---

### 3. Privacy Diagnostics (`POST /privacy/process`)
Inspects how a query is scrubbed, redacted, and minimized.

```bash
curl -X POST http://localhost:8000/privacy/process \
  -H "Content-Type: application/json" \
  -d '{"content": "My email is user@example.com and phone is +1 555-0199. How to learn React?"}'
```

Response:
```json
{
  "original_content": "My email is user@example.com...",
  "sanitized_content": "How to learn React?",
  "entities_detected": [
    { "type": "EMAIL", "value": "user@example.com" },
    { "type": "PHONE", "value": "+1 555-0199" }
  ],
  "redacted_count": 2,
  "persist_original": false
}
```

---

### 4. Health Check (`GET /health`)
```bash
curl http://localhost:8000/health
```

---

## 🕷️ Autonomous Crawler & Resumption

### Why NotGoogle Doesn't Lose State
A common issue in web crawlers is losing the frontier queue and indexed documents whenever the server shuts down. NotGoogle implements an atomic dual-storage architecture:

1. **PostgreSQL Document Store**: Every crawled page is stored with its title, snippet, body text, SHA-256 hash, 64-bit SimHash, and extracted outlinks.
2. **Persistent Pickle Index (`search_index.pkl`)**: The BM25 inverted index token frequencies and document postings are saved automatically during application shutdown (`lifespan` hook) and at regular crawl checkpoints.
3. **Smart Resumption (`crawler.resume_from_db()`)**:
   - On backend boot, all URLs already in PostgreSQL are pre-loaded into the crawler's seen cache so they are **never re-fetched**.
   - Unvisited links discovered from previously crawled pages are reloaded into the frontier queue.
   - The crawler picks up right where it left off, continuously expanding the searchable web corpus.

---

## 🧪 Testing & Verification

NotGoogle includes automated unit test suites verifying the privacy boundary, entity redaction, and minimization:

```bash
cd NotGoogle
source .venv/bin/activate

# Run the privacy engine test suite:
python test_privacy.py
```

Expected output:
```text
=== Running NotGoogle Privacy Engine Test Suite ===

✔ [1/5] PII Detection Passed
✔ [2/5] PII Redaction Passed
✔ [3/5] Query Minimization Passed
✔ [4/5] Privacy-Safe Logging & Ephemeral Context Passed
✔ [5/5] External Boundary Leakage Scanner Passed: 0 Leaks Detected

All Privacy Tests Passed Successfully.
```

---

## ⚙️ Configuration & Customization

| Variable | Default Value | Description |
|:---|:---|:---|
| `DATABASE_URL` | `postgresql://postgres:postgrespassword@localhost:5432/notgoogle` | Connection string for PostgreSQL (supports local & Neon Cloud) |
| `SEARXNG_URL` | `http://localhost:8080` | URL of the SearXNG metasearch instance |
| `LLM_MODEL` | `gemini/gemini-2.5-flash` | LiteLLM model identifier (`groq/llama-3.3-70b-versatile`, `gpt-4o-mini`, etc.) |
| `GEMINI_API_KEY` | *(Optional)* | API key for Google Gemini models |
| `GROQ_API_KEY` | *(Optional)* | API key for Groq Cloud inference |
| `OPENAI_API_KEY` | *(Optional)* | API key for OpenAI models |

### Switching LLM Providers
Thanks to LiteLLM, you can switch providers with a single line change in your `.env`:

```env
# Groq Llama 3.3 (Ultra fast inference)
LLM_MODEL=groq/llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# OpenAI GPT-4o Mini
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Local Ollama (100% offline & private)
LLM_MODEL=ollama/llama3
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an issue or submit a pull request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <sub>Crafted with passion for open-source search, user privacy, and neural information retrieval.</sub>
</div>
