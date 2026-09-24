import os
import json
from typing import Optional, AsyncGenerator
import asyncpg
from dotenv import load_dotenv

from app.api.schemas import ExtractedDocument
from app.engine.crawler.dedup import DocumentDeduplicator

load_dotenv()

DEFAULT_LOCAL_DSN = "postgresql://postgres:postgrespassword@localhost:5432/notgoogle"

class PostgresDocumentStore:
    def __init__(self, 
        dsn: Optional[str] = None,
        min_pool_size: int = 1,
        max_pool_size: int = 10):

        self.dsn = dsn or os.getenv("DATABASE_URL") or DEFAULT_LOCAL_DSN
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        is_cloud_db = "neon.tech" in self.dsn or "sslmode=require" in self.dsn
        ssl_mode = "require" if is_cloud_db else False

        clean_dsn = self.dsn.split("?")[0] if is_cloud_db else self.dsn

        self.pool = await asyncpg.create_pool(
            dsn=clean_dsn,
            ssl=ssl_mode,
            min_size=self.min_pool_size,
            max_size=self.max_pool_size,
        )
        await self._init_tables()
        print(f"[PostgresStore] Successfully connected to {'Neon Cloud' if is_cloud_db else 'Local'} Postgres")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def _init_tables(self):

        query = """
        CREATE TABLE IF NOT EXISTS documents (
            id BIGSERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            snippet TEXT NOT NULL,
            text_content TEXT NOT NULL,
            sha256 VARCHAR(64) NOT NULL,
            simhash BIGINT NOT NULL,
            content_length INT NOT NULL,
            outlinks JSONB DEFAULT '[]'::jsonb,
            indexed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_docs_sha256 ON documents (sha256);
        CREATE INDEX IF NOT EXISTS idx_docs_simhash ON documents (simhash);
        CREATE INDEX IF NOT EXISTS idx_docs_indexed ON documents (indexed);
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query)


    async def is_exact_duplicate(self, sha256_hash: str) -> bool:

        query = "SELECT 1 FROM documents WHERE sha256 = $1 LIMIT 1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, sha256_hash)
            return row is not None

    async def find_near_duplicate(
        self, simhash: int, threshold: int = 3
    ) -> Optional[str]:
        query = """
            SELECT url, simhash
            FROM documents
            LIMIT 5000;
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            for row in rows:
                raw_simhash = row["simhash"]
                existing_simhash = raw_simhash & 0xFFFFFFFFFFFFFFFF if raw_simhash is not None else 0
                dist = DocumentDeduplicator.hamming_distance(simhash, existing_simhash)
                if dist <= threshold:
                    return row["url"]
        return None

    async def save_document(self, doc: ExtractedDocument) -> int:
        sha = DocumentDeduplicator.compute_sha256(doc.text_content)
        simhash = DocumentDeduplicator.compute_simhash(doc.text_content)
        signed_simhash = simhash if simhash < (1 << 63) else simhash - (1 << 64)

        query = """
        INSERT INTO documents (
            url, title, snippet, text_content, sha256, simhash,
            content_length, outlinks, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, NOW()
        )
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            snippet = EXCLUDED.snippet,
            text_content = EXCLUDED.text_content,
            sha256 = EXCLUDED.sha256,
            simhash = EXCLUDED.simhash,
            content_length = EXCLUDED.content_length,
            outlinks = EXCLUDED.outlinks,
            updated_at = NOW()
        RETURNING id;
        """
        async with self.pool.acquire() as conn:
            doc_id = await conn.fetchval(
                query,
                doc.url,
                doc.title,
                doc.snippet,
                doc.text_content,
                sha,
                signed_simhash,
                doc.content_length,
                json.dumps(doc.outlinks),
            )
            return doc_id

    async def stream_unindexed_documents(
        self, batch_size: int = 500
    ) -> AsyncGenerator[list[dict], None]:
        """
        Batched streaming cursor to feed the downstream Indexer (Phase 3.6).
        """
        query = """
        SELECT id, url, title, snippet, text_content
        FROM documents
        WHERE indexed = FALSE
        ORDER BY id ASC;
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                cursor = await conn.cursor(query)
                while True:
                    batch = await cursor.fetch(batch_size)
                    if not batch:
                        break
                    yield [dict(row) for row in batch]

    async def mark_as_indexed(self, doc_ids: list[int]):
        if not doc_ids:
            return
        query = "UPDATE documents SET indexed = TRUE WHERE id = ANY($1::bigint[]);"
        async with self.pool.acquire() as conn:
            await conn.execute(query, doc_ids)

    async def get_total_documents(self) -> int:
        query = "SELECT COUNT(*) FROM documents;"
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query)

#testing
async def main():
    store = PostgresDocumentStore()
    await store.connect()

    sample_doc = ExtractedDocument(
        url="https://fastapi.tiangolo.com/tutorial/",
        title="FastAPI First Steps Tutorial",
        snippet="The simplest FastAPI file could look like this...",
        text_content="FastAPI is a modern web framework for Python. To build an app instantiate FastAPI.",
        outlinks=["https://fastapi.tiangolo.com/advanced/"],
        content_length=95,
    )

    # 1. Compute hashes
    sha = DocumentDeduplicator.compute_sha256(sample_doc.text_content)
    simhash = DocumentDeduplicator.compute_simhash(sample_doc.text_content)

    # 2. Check duplicate before saving
    is_dup = await store.is_exact_duplicate(sha)
    print(f"Before insert -> Is exact duplicate: {is_dup}")

    # 3. Save document
    doc_id = await store.save_document(sample_doc)
    print(f"Inserted document with DB ID: {doc_id}")

    # 4. Check duplicate after saving
    is_dup_after = await store.is_exact_duplicate(sha)
    print(f"After insert -> Is exact duplicate: {is_dup_after}")

    # 5. Check Near-Duplicate
    near_dup = await store.find_near_duplicate(simhash, threshold=3)
    print(f"Near-duplicate matched URL: {near_dup}")

    # 6. Check total count
    total = await store.get_total_documents()
    print(f"Total documents in PostgreSQL: {total}")

    await store.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())