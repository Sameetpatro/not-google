import asyncio
from app.engine.crawler.storage import PostgresDocumentStore
from app.engine.vector_store import VectorSearchEngine

async def main():
    db = PostgresDocumentStore()
    await db.connect()

    v_engine = VectorSearchEngine(db_store=db)

    await v_engine.init_vector_extension()
    await v_engine.generate_missing_embeddings(batch_size=100)

    test_query = "how to build a rest api"
    print(f"\n--- Testing Semantic Query: '{test_query}' ---")
    results = await v_engine.search(test_query, top_k=3)
    for res in results:
        print(f"[{res.score}] {res.title} -> {res.url}")
        
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())