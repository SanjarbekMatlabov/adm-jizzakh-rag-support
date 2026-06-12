"""Centralized configuration for the ADM Jizzakh Kia Customer Support Assistant.

All environment-driven settings and static constants are resolved here so the
rest of the codebase can depend on a single, validated source of truth.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load variables from a local .env file if present (no-op on HF Spaces).
load_dotenv()

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Filesystem layout
# --------------------------------------------------------------------------- #
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
VECTOR_DB_DIR: Path = BASE_DIR / "vector_db"
ASSETS_DIR: Path = BASE_DIR / "assets"

# Ensure runtime directories exist.
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    """Strongly typed application settings sourced from environment variables."""

    # --- Secrets / integrations -------------------------------------------- #
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    github_repository: str = field(
        default_factory=lambda: os.getenv("GITHUB_REPOSITORY", "")
    )

    # --- Company information ----------------------------------------------- #
    company_name: str = field(
        default_factory=lambda: os.getenv("COMPANY_NAME", "ADM Jizzakh")
    )
    company_email: str = field(
        default_factory=lambda: os.getenv("COMPANY_EMAIL", "support@adm.uz")
    )
    company_phone: str = field(
        default_factory=lambda: os.getenv("COMPANY_PHONE", "+998551522222")
    )

    # --- Model configuration ----------------------------------------------- #
    chat_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    )
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    )

    # --- RAG tuning -------------------------------------------------------- #
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "150"))
    )
    retrieval_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_K", "5")))

    # --- Behaviour flags --------------------------------------------------- #
    rebuild_index: bool = field(default_factory=lambda: _get_bool("REBUILD_INDEX", False))

    # ----------------------------------------------------------------------- #
    # Derived paths
    # ----------------------------------------------------------------------- #
    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    @property
    def vector_db_dir(self) -> Path:
        return VECTOR_DB_DIR

    @property
    def assets_dir(self) -> Path:
        return ASSETS_DIR

    @property
    def logo_path(self) -> Path:
        return ASSETS_DIR / "logo.png"

    # ----------------------------------------------------------------------- #
    # Validation helpers
    # ----------------------------------------------------------------------- #
    def validate_openai(self) -> None:
        """Raise a clear error when the OpenAI key is missing."""
        if not self.openai_api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to your environment or .env file."
            )

    def github_configured(self) -> bool:
        """Return True when GitHub integration can be used."""
        return bool(self.github_token and self.github_repository)

    def missing_keys(self) -> List[str]:
        """Return a list of important configuration values that are missing."""
        missing: List[str] = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        if not self.github_repository:
            missing.append("GITHUB_REPOSITORY")
        return missing


# Single shared settings instance used across the application.
settings = Settings()


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the whole application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
