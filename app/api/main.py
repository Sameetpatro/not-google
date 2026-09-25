import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import SearchResponse, SearchItem
from app.query.processor import QueryProcessor
from app.engine.indexer import InvertedIndex
from app.engine.bm25 import BM25Ranker
from app.engine.crawler.storage import PostgresDocumentStore
from app.engine.vector_store import VectorSearchEngine
from app.engine.hybrid import HybridRetriever
from app.engine.reranker import DocumentReranker
from app.engine.searxng import SearXNGClient

db_store = PostgresDocumentStore()
index = InvertedIndex(index_file_path="search_index.pkl")
bm25_ranker: BM25Ranker = BM25Ranker(index=index)
vector_engine: VectorSearchEngine = None
hybrid_retriever: HybridRetriever = None
reranker: DocumentReranker = None
searxng_client = SearXNGClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bm25_ranker, vector_engine, hybrid_retriever, reranker

    await db_store.connect()

    # Load serialized index on startup

    index.load_from_disk()
    bm25_ranker = BM25Ranker(index=index)

    vector_engine = VectorSearchEngine(db_store=db_store)

    hybrid_retriever = HybridRetriever(
        bm25_ranker=bm25_ranker,
        vector_engine=vector_engine,
        rrf_k=60,
    )

    reranker = DocumentReranker()
    print("[Lifespan] Hybrid search pipeline successfully initialized!")

    yield
    await db_store.disconnect()

app = FastAPI(
    title="NotGoogle",
    description="Basic endpoint to check query passing",
    version="1.0.1",
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
async def search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(10, ge=1, le=50, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ai_overview: bool = Query(False, description="AI overview toggle"),
    include_searxng: bool = Query(
        False, description="Toggle side-by-side SearXNG web results"
    ),
):

    processed_query = QueryProcessor.process(q)

    # local Search Pipeline
    async def run_local_pipeline() -> list[SearchItem]:
        candidates = await hybrid_retriever.search(
            query=processed_query,
            candidate_pool_size=25,
            top_k=25,
        )
        return reranker.rerank(query=q, candidates=candidates, top_k=max(25, offset + limit))

    # searXNG Web Search
    async def run_searxng_pipeline() -> Optional[list[SearchItem]]:
        if not include_searxng:
            return None
        return await searxng_client.search(query=q, limit=limit)

    # Execute both asynchronously in parallel
    local_results, searxng_results = await asyncio.gather(
        run_local_pipeline(),
        run_searxng_pipeline(),
    )

    paginated_local = local_results[offset : offset + limit]

    return SearchResponse(
        query=q,
        total_res=len(local_results),
        ai_overview=None,
        resp=paginated_local,
        searxng_resp=searxng_results,
    )

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "indexed_bm25_docs": index.total_docs,
        "hybrid_ready": hybrid_retriever is not None,
        "reranker_ready": reranker is not None,
    }