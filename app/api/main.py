import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import SearchResponse, SearchItem, AIOverviewPayload
from app.query.processor import QueryProcessor
from app.engine.indexer import InvertedIndex
from app.engine.bm25 import BM25Ranker
from app.engine.crawler.storage import PostgresDocumentStore
from app.engine.vector_store import VectorSearchEngine
from app.engine.hybrid import HybridRetriever
from app.engine.reranker import DocumentReranker
from app.engine.searxng import SearXNGClient
from app.engine.overview import AIOverviewGenerator
from app.privacy.service import PrivacyService, PrivacyProcessResult

# Pipeline Singletons
db_store = PostgresDocumentStore()
index = InvertedIndex(index_file_path="search_index.pkl")
bm25_ranker: Optional[BM25Ranker] = None
vector_engine: Optional[VectorSearchEngine] = None
hybrid_retriever: Optional[HybridRetriever] = None
reranker: Optional[DocumentReranker] = None
searxng_client = SearXNGClient()
overview_generator = AIOverviewGenerator()
privacy_service = PrivacyService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bm25_ranker, vector_engine, hybrid_retriever, reranker

    await db_store.connect()

    index.load_from_disk()
    bm25_ranker = BM25Ranker(index=index)
    vector_engine = VectorSearchEngine(db_store=db_store)
    hybrid_retriever = HybridRetriever(
        bm25_ranker=bm25_ranker,
        vector_engine=vector_engine,
        rrf_k=60,
    )
    reranker = DocumentReranker()

    print("[Lifespan] NotGoogle with Privacy Boundary operational!")
    yield
    await db_store.disconnect()
    await searxng_client.close()


app = FastAPI(
    title="NotGoogle Search Engine",
    description="Privacy-Preserving Search Engine with Hybrid Retrieval & Local Reranking",
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


@app.post("/privacy/process", response_model=PrivacyProcessResult)
def process_privacy(
    content: str = Body(..., embed=True, description="Query or text to evaluate"),
    operation: str = Body("search", embed=True, description="Target operation type"),
):
    """Internal diagnostic endpoint: runs PII detection, redaction, and minimization."""
    return privacy_service.process_query(content=content, operation=operation)


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(10, ge=1, le=50, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ai_overview: bool = Query(False, description="Generate AI Overview summary"),
    include_searxng: bool = Query(
        False, description="Toggle side-by-side SearXNG web results"
    ),
):
    # 1. PRIVACY LAYER: PII Detection, Redaction & Minimization
    privacy_result = privacy_service.process_query(content=q, operation="search")
    sanitized_query = privacy_result.sanitized_content

    # 2. Query Processing (on sanitized query)
    processed_query = QueryProcessor.process(sanitized_query)

    # Coroutine 1: Local Hybrid Search + Cross-Encoder Reranker
    async def run_local_pipeline() -> list[SearchItem]:
        candidates = await hybrid_retriever.search(
            query=processed_query,
            candidate_pool_size=25,
            top_k=25,
        )
        return reranker.rerank(
            query=sanitized_query,
            candidates=candidates,
            top_k=max(25, offset + limit),
        )

    # Coroutine 2: External SearXNG Web Pipeline (Receives ONLY the sanitized query)
    async def run_searxng_pipeline() -> Optional[list[SearchItem]]:
        if not (include_searxng or ai_overview):
            return None
        # EXTERNAL BOUNDARY ENFORCEMENT: SearXNG never sees original raw query
        return await searxng_client.search(query=sanitized_query, limit=limit)

    # Execute search channels concurrently
    local_results, searxng_results = await asyncio.gather(
        run_local_pipeline(),
        run_searxng_pipeline(),
    )

    # Coroutine 3: AI Overview (Receives sanitized query + scrubbed context)
    overview_payload: Optional[AIOverviewPayload] = None
    if ai_overview:
        overview_payload = await overview_generator.generate_overview(
            query=sanitized_query,
            local_results=local_results,
            web_results=searxng_results,
        )

    display_searxng = searxng_results if include_searxng else None
    paginated_local = local_results[offset : offset + limit]

    return SearchResponse(
        query=sanitized_query,
        total_res=len(local_results),
        ai_overview=overview_payload,
        resp=paginated_local,
        searxng_resp=display_searxng,
    )


@app.get("/health")
async def health_check():
    searxng_health = await searxng_client.check_health()
    return {
        "status": "ok",
        "indexed_bm25_docs": index.total_docs,
        "hybrid_ready": hybrid_retriever is not None,
        "reranker_ready": reranker is not None,
        "privacy_layer": "active",
        "searxng": searxng_health,
    }