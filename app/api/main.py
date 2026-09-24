from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import SearchResponse, SearchItem
from app.query.processor import QueryProcessor
from app.engine.indexer import InvertedIndex
from app.engine.bm25 import BM25Ranker

index = InvertedIndex(index_file_path="search_index.pkl")
ranker: BM25Ranker = BM25Ranker(index=index)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ranker
    # Load serialized index on startup
    loaded = index.load_from_disk()
    if loaded:
        print(f"[Lifespan] Loaded {index.total_docs} indexed documents.")
    else:
        print("[Lifespan] No index file found on disk. Run sync_indexer first.")
    
    ranker = BM25Ranker(index=index)
    yield


app = FastAPI(
    title="NotGoogle",
    description="Basic endpoint to check query passing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOCK_INDEX = [
    {
        "id": "1",
        "title": "FastAPI Documentation",
        "url": "https://fastapi.tiangolo.com",
        "snippet": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
    },
    {
        "id": "2",
        "title": "Python Official Documentation",
        "url": "https://docs.python.org",
        "snippet": "Official documentation for the Python programming language.",
    },
    {
        "id": "3",
        "title": "Building a Search Engine in Python",
        "url": "https://example.com/search-engine-guide",
        "snippet": "Learn inverted indexes, tokenization, BM25 ranking, and vector search.",
    },
]


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="your query"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    ai_overview: bool = Query(False, description="Ai overview toggle")
):
    processed_query = QueryProcessor.process(q)

    ranked_results = ranker.search(processed_query.filtered_tokens, top_k=50)
    paginated_results = ranked_results[offset : offset + limit]

    return SearchResponse(
        query=q,
        total_res=len(ranked_results),
        ai_overview=None,
        resp=paginated_results,
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}