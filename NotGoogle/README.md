# NotGoogle Backend Engine & API Service

This directory houses the core FastAPI backend, retrieval engines, neural models, privacy guard, and autonomous crawler for **NotGoogle**.

> 💡 For full project documentation, quickstart guide, and architectural diagrams, please see the [Root README](../README.md).

---

## 🏛️ Architecture Overview

The backend is built around a high-performance modular pipeline:

1. **Privacy Guard (`app/privacy/`)**:
   - `detector.py`: Scans text using regex patterns for Emails, Phone Numbers, IPv4/IPv6 addresses, API keys (`sk-...`), and passwords.
   - `minimizer.py`: Performs query minimization, stripping non-essential conversational padding.
   - `service.py`: Orchestrates sanitization before search execution or external LLM dispatch.

2. **Retrieval & Ranking Stack (`app/engine/`)**:
   - `indexer.py` & `bm25.py`: High-performance inverted index with token normalization, term frequency scoring, and pickle serialization.
   - `vector_store.py`: Semantic vector search engine utilizing `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings) and PostgreSQL `pgvector` with HNSW indexing.
   - `hybrid.py`: Reciprocal Rank Fusion (RRF with $k=60$) combining BM25 keyword rankings with dense semantic vector distances.
   - `reranker.py`: Deep cross-attention neural reranking via `cross-encoder/ms-marco-MiniLM-L-6-v2` with Sigmoid normalization.
   - `searxng.py`: Asynchronous client for SearXNG metasearch, providing real-time web discovery.
   - `overview.py`: Search Generative Experience (SGE) AI Overview generator powered by LiteLLM with strict inline citation attribution.

3. **Autonomous Crawler & Ingestion (`app/engine/crawler/`)**:
   - `pipeline.py`: Asynchronous 24/7 background crawler with auto-replenishing frontier.
   - `frontier.py`: Politeness-aware domain rate limiter and FIFO/priority URL queue.
   - `extractor.py`: HTML text parser and outlink extractor using BeautifulSoup4.
   - `dedup.py`: Near-duplicate detection via 64-bit SimHash (Hamming distance $\le 3$) and exact matching via SHA-256.
   - `storage.py`: Async PostgreSQL storage manager with automatic table migration and restart resumption.

---

## 🚀 Running the Backend

### 1. Prerequisites
- Python 3.11+ (Python 3.13+ recommended)
- Running PostgreSQL database (or Neon Cloud) with `pgvector`
- Running SearXNG instance (via Docker Compose)

### 2. Setup & Run
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verify Privacy Test Suite
```bash
python test_privacy.py
```