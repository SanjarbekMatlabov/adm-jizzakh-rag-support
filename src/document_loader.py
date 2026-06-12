"""Document loading and chunking for the knowledge base.

Loads every PDF found in the data directory using ``PyPDFLoader``, preserves
``source`` and ``page`` metadata, and splits the content into overlapping
chunks with ``RecursiveCharacterTextSplitter``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.utils import safe_filename

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads and splits the knowledge-base documents."""

    def __init__(
        self,
        data_dir: Path | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir else settings.data_dir
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #
    def discover_pdfs(self) -> List[Path]:
        """Return all PDF files inside the data directory."""
        if not self.data_dir.exists():
            logger.warning("Data directory does not exist: %s", self.data_dir)
            return []
        pdfs = sorted(self.data_dir.glob("*.pdf"))
        logger.info("Discovered %d PDF document(s) in %s", len(pdfs), self.data_dir)
        return pdfs

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def load_single_pdf(self, path: Path) -> List[Document]:
        """Load one PDF into page-level documents with normalized metadata."""
        try:
            loader = PyPDFLoader(str(path))
            pages = loader.load()
        except Exception as exc:  # noqa: BLE001 - surface a clean message
            logger.error("Failed to load PDF '%s': %s", path.name, exc)
            return []

        documents: List[Document] = []
        for page in pages:
            text = (page.page_content or "").strip()
            if not text:
                continue  # Skip empty / image-only pages.
            # PyPDFLoader provides a 0-indexed "page" entry; preserve it.
            page_number = page.metadata.get("page", 0)
            page.metadata["source"] = safe_filename(path.name)
            page.metadata["page"] = page_number
            documents.append(page)

        logger.info("Loaded %d non-empty page(s) from %s", len(documents), path.name)
        return documents

    def load_all(self) -> List[Document]:
        """Load every PDF in the data directory."""
        all_docs: List[Document] = []
        pdfs = self.discover_pdfs()
        if not pdfs:
            logger.warning("No PDF documents found to load.")
            return []
        for pdf in pdfs:
            all_docs.extend(self.load_single_pdf(pdf))
        logger.info("Loaded %d total page-documents.", len(all_docs))
        return all_docs

    # ------------------------------------------------------------------ #
    # Splitting
    # ------------------------------------------------------------------ #
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split page-level documents into overlapping chunks."""
        if not documents:
            return []
        chunks = self._splitter.split_documents(documents)
        # Guarantee metadata survives the split.
        for chunk in chunks:
            chunk.metadata.setdefault("source", "unknown")
            chunk.metadata.setdefault("page", 0)
        logger.info("Split documents into %d chunk(s).", len(chunks))
        return chunks

    def load_and_split(self) -> List[Document]:
        """Convenience method: load all PDFs and return chunks."""
        return self.split_documents(self.load_all())
