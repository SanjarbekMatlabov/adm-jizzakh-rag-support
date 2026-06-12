"""Offline utility to (re)build the FAISS vector index from the PDFs in ./data.

Usage:
    python build_index.py            # build if missing
    python build_index.py --rebuild  # force a full rebuild
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.config import configure_logging, settings
from src.vector_store import VectorStoreManager

logger = logging.getLogger("build_index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the FAISS knowledge index.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force a full rebuild even if an index already exists.",
    )
    args = parser.parse_args()

    configure_logging(logging.INFO)

    try:
        settings.validate_openai()
    except EnvironmentError as exc:
        logger.error(str(exc))
        return 1

    pdfs = sorted(settings.data_dir.glob("*.pdf"))
    if not pdfs:
        logger.error(
            "No PDF documents found in %s. Add the Kia manuals and the ADM FAQ "
            "before building the index.",
            settings.data_dir,
        )
        return 1

    logger.info("Found %d PDF document(s).", len(pdfs))
    manager = VectorStoreManager()
    manager.get_or_create(force_rebuild=args.rebuild)
    logger.info("Vector index is ready in %s", settings.vector_db_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
