import math
import pickle
import os
from collections import defaultdict
from typing import Optional
from dataclasses import dataclass, field

from app.query.processor import QueryProcessor
from app.engine.crawler.storage import PostgresDocumentStore

@dataclass
class Posting:
    doc_id: str
    term_freq: int


@dataclass
class DocumentMetadata:
    doc_id: str
    title: str
    url: str
    snippet: str
    length: int 


class InvertedIndex:
    def __init__(self, index_file_path: str = "search_index.pkl"):
        self.index_file_path = index_file_path

        self.postings: dict[str, list[Posting]] = defaultdict(list)
        self.doc_store: dict[str, DocumentMetadata] = {}

        self.total_docs: int = 0
        self.total_tokens: int = 0
        self.avg_doc_len: float = 0.0

    def add_document(self, doc_id: str, title: str, url: str, snippet: str, text_content: str):
        if doc_id in self.doc_store:
            return
        title_tokens = QueryProcessor.clean_text(title).split()
        body_tokens = QueryProcessor.clean_text(text_content).split()

        all_tokens = title_tokens + body_tokens
        doc_len = len(all_tokens)

        if doc_len == 0:
            return

        tf_map: dict[str, int] = defaultdict(int)

        for t in body_tokens:
            tf_map[t] += 1

        for t in title_tokens:
            tf_map[t] += 3

        #append it to inverted list

        for term, tf in tf_map.items():
            self.postings[term].append(Posting(doc_id=doc_id, term_freq=tf))

        #store metadata in forward index
        self.doc_store[doc_id] = DocumentMetadata(
            doc_id=doc_id,
            title=title,
            url=url,
            snippet=snippet,
            length=doc_len,
        )

        #final corpus vals
        self.total_docs += 1
        self.total_tokens += doc_len
        self.avg_doc_len = self.total_tokens / self.total_docs

    def get_postings(self, term: str) -> list[Posting]:
        return self.postings.get(term, [])

    def get_doc_freq(self, term: str) -> int:
        return len(self.postings.get(term, []))
    
    def save_to_disk(self):
        data = {
            "postings": dict(self.postings),
            "doc_store": self.doc_store,
            "total_docs": self.total_docs,
            "total_tokens": self.total_tokens,
            "avg_doc_len": self.avg_doc_len,
        }
        with open(self.index_file_path, "wb") as f:
            pickle.dump(data, f)
        print(f"[Indexer] Saved inverted index with {self.total_docs} docs to {self.index_file_path}")

    def load_from_disk(self) -> bool:
        if not os.path.exists(self.index_file_path):
            return False
        with open(self.index_file_path, "rb") as f:
            data = pickle.load(f)
            self.postings = defaultdict(list, data["postings"])
            self.doc_store = data["doc_store"]
            self.total_docs = data["total_docs"]
            self.total_tokens = data["total_tokens"]
            self.avg_doc_len = data["avg_doc_len"]
        print(f"[Indexer] Loaded inverted index with {self.total_docs} docs from {self.index_file_path}")
        return True