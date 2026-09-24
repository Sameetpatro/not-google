import json
import asyncio
from typing import Optional
import asyncpg
from sentence_transformers import SentenceTransformer

from app.api.schemas import SearchItem
from app.engine.crawler.storage import PostgresDocumentStore

class VectorSearchEngine:
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DIMENSION = 384

    def __init__(self, db_store: PostgresDocumentStore):
        self.db_store = db_store
        self.db = db_store
        self.model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        if self.model is None:
            print("[VectorEngine] Loading embedding model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer(self.MODEL_NAME)
        return self.model

    def encode(self, text: str) -> list[float]:
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def init_vector_extension(self):
        query = f"""
        CREATE EXTENSION IF NOT EXISTS vector;

        ALTER TABLE documents 
        ADD COLUMN IF NOT EXISTS embedding vector({self.DIMENSION});

        CREATE INDEX IF NOT EXISTS idx_docs_embedding_hnsw 
        ON documents USING hnsw (embedding vector_cosine_ops);
        """
        async with self.db.pool.acquire() as conn:
            await conn.execute(query)
            print("[VectorEngine] pgvector extension and HNSW index initialized.")


    async def generate_missing_embeddings(self, batch_size: int = 50):
        select_query = """
        SELECT id, title, snippet, text_content
        FROM documents
        WHERE embedding IS NULL
        LIMIT $1;
        """
        update_query = """
        UPDATE documents
        SET embedding = $1::vector
        WHERE id = $2;
        """
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(select_query, batch_size)
            if not rows:
                print("[VectorEngine] No missing embeddings to generate.")
                return

            print(f"[VectorEngine] Generating embeddings for {len(rows)} documents...")
            for row in rows:
                doc_id = row["id"]

                text_to_embed = f"{row['title']}. {row['snippet']}"
                vec = self.encode(text_to_embed)

                vec_str = json.dumps(vec)
                await conn.execute(update_query, vec_str, doc_id)

            print(f"[VectorEngine] Successfully saved {len(rows)} embeddings to Neon.")

    async def search(self, query_text: str, top_k: int = 10) -> list[SearchItem]:
        query_vec = self.encode(query_text)
        query_vec_str = json.dumps(query_vec)
        sql = """
        SELECT 
            id, 
            url, 
            title, 
            snippet, 
            1 - (embedding <=> $1::vector) AS similarity_score
        FROM documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector ASC
        LIMIT $2;
        """
        results: list[SearchItem] = []
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(sql, query_vec_str, top_k)
            for row in rows:
                score = float(row["similarity_score"])
                results.append(
                    SearchItem(
                        id=str(row["id"]),
                        title=row["title"],
                        url=row["url"],
                        snippet=row["snippet"],
                        score=round(score, 4),
                        source="local_vector",
                    )
                )
        return results