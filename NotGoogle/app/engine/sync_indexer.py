import asyncio
from app.engine.crawler.storage import PostgresDocumentStore
from app.engine.indexer import InvertedIndex

async def run_indexer_pipeline(index_file_path: str = "search_index.pkl"):
    pg = PostgresDocumentStore()
    await pg.connect()

    index = InvertedIndex(index_file_path=index_file_path)

    index.load_from_disk()

    indexed_ids: list[int] = []
    print("[SyncIndexer] Checking for unindexed documents in Neon/Postgres...")

    async for batch in pg.stream_unindexed_documents(batch_size=200):
        for doc in batch:
            doc_id_str = str(doc["id"])
            index.add_document(
                doc_id=doc_id_str,
                title=doc["title"],
                url=doc["url"],
                snippet=doc["snippet"],
                text_content=doc["text_content"],
            )
            indexed_ids.append(doc["id"])

        print(f"[SyncIndexer] Processed batch of {len(batch)} documents.")

    if indexed_ids:
        await pg.mark_as_indexed(indexed_ids)
        index.save_to_disk()
        print(f"[SyncIndexer] Successfully indexed {len(indexed_ids)} new documents!")

    else:
        print("[SyncIndexer] All documents are already indexed.")

    await pg.disconnect()


if __name__ == "__main__":
    asyncio.run(run_indexer_pipeline())