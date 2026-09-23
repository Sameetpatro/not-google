from typing import Optional
from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    id: str = Field(..., description="Unique document ID or hash")
    title: str = Field(..., description="Title of the document")
    url: str = Field(..., description="Target URL")
    snippet: str = Field(..., description="Highlighted or summary snippet")
    score: float = Field(default=0.0, description="Relevance or rank score")
    source: str = Field(default="local", description="Provider origin: 'local' or 'searxng'")


class SearchResponse(BaseModel):
    query: str = Field(..., description="Original raw or normalized query")
    total_res: int = Field(..., description="Count of matched items")
    ai_overview: Optional[str] = Field(default=None, description="Synthesized AI overview if requested")
    resp: list[SearchItem] = Field(default_factory=list, description="Ranked list of results")


class ProcessedQuery(BaseModel):
    raw_query: str = Field(..., description="Original raw user input")
    normalized_query: str = Field(..., description="Cleaned, lowercase query without punctuation")
    tokens: list[str] = Field(default_factory=list, description="Extracted word tokens")
    filtered_tokens: list[str] = Field(default_factory=list, description="Tokens with stop words removed")
    is_question: bool = Field(default=False, description="Whether the query is informational/question-based")