# NotGoogle

A privacy-preserving hybrid search engine combining BM25 lexical search, pgvector semantic retrieval, cross-encoder neural reranking, LiteLLM AI Overviews, and an autonomous background web crawler.

---

## 🏛️ Architecture

```mermaid
flowchart TD
    Query([User Query]) --> Privacy[Privacy Guard: PII Redaction & Minimization]
    Privacy --> CleanQ[Sanitized Query]

    subgraph Retrieval["1. Hybrid Retrieval & Reranking"]
        CleanQ --> BM25[BM25 Inverted Index]
        CleanQ --> Vec[pgvector HNSW Store]
        BM25 --> RRF[Reciprocal Rank Fusion k=60]
        Vec --> RRF
        RRF --> CrossEnc[Cross-Encoder Reranker]
    end

    subgraph Web["2. External Web Discovery"]
        CleanQ --> SearXNG[SearXNG Meta-Search]
        SearXNG --> WebResults[Live Web Results]
        WebResults -. Outlinks .-> Frontier[(URL Frontier Queue)]
    end

    subgraph Crawler["3. 24/7 Autonomous Crawler"]
        Frontier --> Fetcher[HTTP Async Fetcher]
        Fetcher --> Extractor[HTML Extractor]
        Extractor --> Dedup{SimHash & SHA-256}
        Dedup -- Unique --> Storage[(PostgreSQL + BM25 Index)]
        Extractor -. Discovered Links .-> Frontier
    end

    CrossEnc --> Synthesizer[Result Synthesizer]
    WebResults --> Synthesizer
    Synthesizer --> SGE[LiteLLM AI Overview]
    Synthesizer --> Frontend[React 19 UI]
    SGE --> Frontend
```

---

## 📐 Retrieval & Ranking Formulas

### 1. BM25 Lexical Ranking
Used for keyword matching over tokenized inverted indexes ($k_1 = 1.5, b = 0.75$):

$$\text{IDF}(q) = \ln\left(1 + \frac{N - n(q) + 0.5}{n(q) + 0.5}\right)$$

$$\text{Score}_{\text{BM25}}(D, Q) = \sum_{q \in Q} \text{IDF}(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

Where:
- $N$ = total documents in index
- $n(q)$ = document frequency of query term $q$
- $f(q, D)$ = term frequency of $q$ in document $D$
- $|D|$ and $\text{avgdl}$ = document length and average document length in the corpus

---

### 2. Dense Semantic Vector Search
Embeddings generated via `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors). Cosine similarity is computed over PostgreSQL `pgvector` HNSW indexes:

$$\text{CosineSim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = \frac{\sum_{i=1}^{d} u_i v_i}{\sqrt{\sum_{i=1}^{d} u_i^2} \sqrt{\sum_{i=1}^{d} v_i^2}}$$

---

### 3. Reciprocal Rank Fusion (RRF)
Merges ranked lists from lexical (BM25) and semantic (dense vector) retrieval into a single unified candidate pool using smoothing constant $k = 60$:

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{BM25}, \text{Vector}\}} \frac{1}{k + r_m(d)}$$

Where $r_m(d) \in \{1, 2, \dots\}$ represents the 1-based rank of document $d$ within retrieval system $m$.

---

### 4. Cross-Encoder Neural Reranking
Joint query-document cross-attention using `cross-encoder/ms-marco-MiniLM-L-6-v2`. Raw logits $z$ are normalized to confidence scores in $[0, 1]$ via the Sigmoid function:

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

---

### 5. SimHash Near-Duplicate Content Detection
Identifies near-duplicate web documents by projecting 64-bit token hashes into a binary fingerprint $h(D) \in \{0, 1\}^{64}$. Near-duplicates are filtered if the Hamming distance $H$ is within threshold:

$$H(h_1, h_2) = \text{popcount}(h_1 \oplus h_2) \le 3$$

---

## 📂 Project Structure

```
NotGoogle/
├── NotGoogle/                     # Backend Service (FastAPI)
│   ├── app/
│   │   ├── api/                   # API routes (/search, /crawler, /health)
│   │   ├── engine/                # BM25, pgvector, RRF, Cross-Encoder, LiteLLM
│   │   │   └── crawler/           # Frontier queue, extractor, SimHash, storage
│   │   ├── privacy/               # PII detector, redactor, query minimizer
│   │   └── query/                 # Query normalization & tokenizer
│   ├── docker-compose.yaml        # SearXNG service
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Environment variables template
│
├── frontend/                      # Frontend Application (React 19 + Vite)
│   ├── src/                       # Google-authentic UI & SGE components
│   └── package.json               # Node dependencies
│
├── start.sh                       # One-click startup script (Docker + Backend + Frontend)
├── stop.sh                        # One-click graceful stop script
└── README.md
```

---

## 🚀 How to Use

### 1. Configure Environment
```bash
cp NotGoogle/.env.example NotGoogle/.env
```
Fill in your credentials in `NotGoogle/.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/notgoogle
SEARXNG_URL=http://localhost:8080
LLM_MODEL=gemini/gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Start Everything
Run the unified startup script from the root directory:
```bash
./start.sh
```
This automatically:
- Checks Docker and starts SearXNG on `http://localhost:8080`.
- Sets up `.venv`, initializes DB/models, and starts FastAPI on `http://localhost:8000`.
- Launches Vite React frontend on `http://localhost:5173`.

### 3. Stop Everything
Press `Ctrl+C` in the running terminal, or run:
```bash
./stop.sh
```
