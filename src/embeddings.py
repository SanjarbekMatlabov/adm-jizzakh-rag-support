"""Embedding model factory.

Wraps the OpenAI embedding model so the rest of the codebase has a single,
validated entry point for constructing embeddings.
"""

from __future__ import annotations

import logging

from langchain_openai import OpenAIEmbeddings

from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Factory and cache for the OpenAI embeddings client."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.embedding_model
        self._client: OpenAIEmbeddings | None = None

    def get_embeddings(self) -> OpenAIEmbeddings:
        """Return a configured ``OpenAIEmbeddings`` instance (lazily created)."""
        if self._client is None:
            settings.validate_openai()
            logger.info("Initializing OpenAI embeddings model: %s", self.model)
            self._client = OpenAIEmbeddings(
                model=self.model,
                api_key=settings.openai_api_key,
            )
        return self._client


def get_embedding_model(model: str | None = None) -> OpenAIEmbeddings:
    """Module-level helper to obtain a configured embeddings client."""
    return EmbeddingProvider(model).get_embeddings()
