"""FAISS vector store management.

Builds, persists and loads a FAISS index over the chunked knowledge base and
exposes a similarity-search helper that returns documents with scores.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.config import settings
from src.document_loader import DocumentLoader
from src.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

INDEX_NAME = "kia_support_index"


class VectorStoreManager:
    """Create, persist, load and query the FAISS vector store."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        embeddings: Optional[OpenAIEmbeddings] = None,
    ) -> None:
        self.persist_dir = Path(persist_dir) if persist_dir else settings.vector_db_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings = embeddings or get_embedding_model()
        self._store: Optional[FAISS] = None

    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    def _index_exists(self) -> bool:
        faiss_file = self.persist_dir / f"{INDEX_NAME}.faiss"
        pkl_file = self.persist_dir / f"{INDEX_NAME}.pkl"
        return faiss_file.exists() and pkl_file.exists()

    # ------------------------------------------------------------------ #
    # Build / load
    # ------------------------------------------------------------------ #
    def build(self, chunks: List[Document]) -> FAISS:
        """Build a FAISS index from document chunks and persist it."""
        if not chunks:
            raise ValueError(
                "Cannot build a vector store from an empty document set. "
                "Ensure PDF documents exist in the data directory."
            )
        logger.info("Building FAISS index from %d chunk(s)...", len(chunks))
        self._store = FAISS.from_documents(chunks, self._embeddings)
        self.save()
        return self._store

    def save(self) -> None:
        """Persist the current index to disk."""
        if self._store is None:
            raise RuntimeError("No vector store to save. Build or load it first.")
        self._store.save_local(str(self.persist_dir), index_name=INDEX_NAME)
        logger.info("Saved FAISS index to %s", self.persist_dir)

    def load(self) -> FAISS:
        """Load a previously persisted index from disk."""
        if not self._index_exists():
            raise FileNotFoundError(
                f"No FAISS index found in {self.persist_dir}. Build it first."
            )
        logger.info("Loading FAISS index from %s", self.persist_dir)
        self._store = FAISS.load_local(
            str(self.persist_dir),
            self._embeddings,
            index_name=INDEX_NAME,
            allow_dangerous_deserialization=True,
        )
        return self._store

    def get_or_create(self, force_rebuild: bool = False) -> FAISS:
        """Load the index if present, otherwise build it from the data dir."""
        if not force_rebuild and self._index_exists():
            try:
                return self.load()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load index (%s). Rebuilding...", exc)

        loader = DocumentLoader()
        chunks = loader.load_and_split()
        return self.build(chunks)

    # ------------------------------------------------------------------ #
    # Querying
    # ------------------------------------------------------------------ #
    def similarity_search(
        self, query: str, k: int | None = None
    ) -> List[Tuple[Document, float]]:
        """Return the top-k most similar documents with their scores."""
        if self._store is None:
            self.get_or_create()
        k = k or settings.retrieval_k
        try:
            return self._store.similarity_search_with_score(query, k=k)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.error("Similarity search failed: %s", exc)
            return []

    @property
    def store(self) -> Optional[FAISS]:
        return self._store
