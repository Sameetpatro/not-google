from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.query.processor import QueryProcessor
from app.api.schemas import SearchResponse, SearchItem

app = FastAPI(
    title="NotGoogle",
    description="Basic endpoint to check query passing",
    version="1.0.0",
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
        "id": 1,
        "title": "FastAPI Documentation",
        "url": "https://fastapi.tiangolo.com",
        "snippet": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
    },
    {
        "id": 2,
        "title": "Python Official Documentation",
        "url": "https://docs.python.org",
        "snippet": "Official documentation for the Python programming language.",
    },
    {
        "id": 3,
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
    print(f"Processed Query: {processed_query}")

    search_terms = processed_query.filtered_tokens

    matched_res = []
    for item in MOCK_INDEX:
        content = f"{item['title']} {item['snippet']}".lower()
        if any(term in content for term in search_terms):
            matched_res.append(item)

    if ai_overview:
        pass

    paginated_results = matched_res[offset : offset + limit]

    return {
        "query": q,
        "total_res": len(matched_res),
        "ai_overview": None,
        "resp": paginated_results,
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}