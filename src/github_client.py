"""Thin GitHub Issues API client used for support ticket creation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from src.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 20  # seconds


class GitHubError(Exception):
    """Raised when a GitHub API call fails."""


@dataclass
class IssueResult:
    """Result of creating a GitHub issue."""

    number: int
    url: str
    title: str


class GitHubClient:
    """Minimal GitHub Issues API wrapper."""

    def __init__(
        self,
        token: Optional[str] = None,
        repository: Optional[str] = None,
    ) -> None:
        self.token = token if token is not None else settings.github_token
        self.repository = (
            repository if repository is not None else settings.github_repository
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def is_configured(self) -> bool:
        return bool(self.token and self.repository)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ------------------------------------------------------------------ #
    # API operations
    # ------------------------------------------------------------------ #
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> IssueResult:
        """Create a GitHub issue and return its number and URL."""
        if not self.is_configured():
            raise GitHubError(
                "GitHub integration is not configured. Set GITHUB_TOKEN and "
                "GITHUB_REPOSITORY environment variables."
            )

        url = f"{GITHUB_API_BASE}/repos/{self.repository}/issues"
        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error("Network error contacting GitHub: %s", exc)
            raise GitHubError(f"Network error contacting GitHub: {exc}") from exc

        if response.status_code == 201:
            data = response.json()
            logger.info("Created GitHub issue #%s", data.get("number"))
            return IssueResult(
                number=data.get("number", 0),
                url=data.get("html_url", ""),
                title=data.get("title", title),
            )

        # Surface a clear, actionable error.
        message = self._extract_error(response)
        logger.error(
            "GitHub issue creation failed (%s): %s", response.status_code, message
        )
        raise GitHubError(
            f"GitHub API error {response.status_code}: {message}"
        )

    @staticmethod
    def _extract_error(response: requests.Response) -> str:
        try:
            data = response.json()
            return data.get("message", response.text)
        except ValueError:
            return response.text or "Unknown error"
