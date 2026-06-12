"""Retrieval Augmented Generation engine.

Wraps the vector store and turns similarity-search results into a context
string plus structured citations consumed by the chatbot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from src.config import settings
from src.prompts import NO_RESULTS_MESSAGE
from src.utils import format_page, safe_filename
from src.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A single source citation."""

    source: str
    page: str
    score: float = 0.0

    def render(self) -> str:
        return f"Source: {self.source}\nPage: {self.page}"


@dataclass
class RetrievalResult:
    """Outcome of a retrieval call."""

    context: str
    citations: List[Citation] = field(default_factory=list)
    found: bool = False

    def citations_markdown(self) -> str:
        """Render citations as a markdown block."""
        if not self.citations:
            return ""
        lines = ["", "**Sources:**"]
        for c in self.citations:
            lines.append(f"- `{c.source}` — page {c.page}")
        return "\n".join(lines)


class RAGEngine:
    """High-level retrieval interface used by the chatbot."""

    def __init__(self, vector_manager: Optional[VectorStoreManager] = None) -> None:
        self.vector_manager = vector_manager or VectorStoreManager()

    def initialize(self, force_rebuild: bool = False) -> None:
        """Ensure the vector store is ready (build or load)."""
        self.vector_manager.get_or_create(force_rebuild=force_rebuild)

    def search(self, query: str, k: int | None = None) -> RetrievalResult:
        """Run similarity search and assemble context + citations."""
        if not query or not query.strip():
            return RetrievalResult(context=NO_RESULTS_MESSAGE, found=False)

        k = k or settings.retrieval_k
        results = self.vector_manager.similarity_search(query, k=k)

        if not results:
            logger.info("No documents retrieved for query: %s", query)
            return RetrievalResult(context=NO_RESULTS_MESSAGE, found=False)

        context_blocks: List[str] = []
        citations: List[Citation] = []
        seen_citations: set = set()

        for doc, score in results:
            source = safe_filename(doc.metadata.get("source", "unknown"))
            page = format_page(doc.metadata.get("page", "N/A"))
            citation_key = (source, page)

            context_blocks.append(
                f"[Source: {source} | Page: {page}]\n{doc.page_content.strip()}"
            )

            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                citations.append(
                    Citation(source=source, page=page, score=float(score))
                )

        context = "\n\n---\n\n".join(context_blocks)
        return RetrievalResult(context=context, citations=citations, found=True)
