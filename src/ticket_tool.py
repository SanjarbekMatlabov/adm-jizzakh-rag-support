"""Support ticket creation logic built on top of the GitHub client."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.config import settings
from src.github_client import GitHubClient, GitHubError
from src.utils import is_valid_email

logger = logging.getLogger(__name__)


@dataclass
class TicketResult:
    """Outcome of a ticket creation attempt."""

    success: bool
    message: str
    url: Optional[str] = None
    number: Optional[int] = None


class SupportTicketService:
    """Validates input and creates support tickets as GitHub Issues."""

    def __init__(self, github_client: Optional[GitHubClient] = None) -> None:
        self.github = github_client or GitHubClient()

    def _build_body(
        self, user_name: str, user_email: str, description: str
    ) -> str:
        """Compose the GitHub issue body in the required format."""
        return (
            f"Name: {user_name}\n"
            f"Email: {user_email}\n\n"
            f"Description: {description}\n\n"
            "---\n"
            f"_Ticket created automatically by the {settings.company_name} "
            "Kia Customer Support AI Assistant._"
        )

    def create_ticket(
        self,
        user_name: str,
        user_email: str,
        title: str,
        description: str,
    ) -> TicketResult:
        """Validate the request and create a GitHub issue."""
        # --- Input validation --------------------------------------- #
        if not user_name or not user_name.strip():
            return TicketResult(False, "A customer name is required to open a ticket.")
        if not is_valid_email(user_email):
            return TicketResult(
                False,
                f"The email address '{user_email}' is not valid. Please provide a "
                "valid email so we can follow up.",
            )
        if not title or not title.strip():
            return TicketResult(False, "A ticket title is required.")
        if not description or not description.strip():
            return TicketResult(False, "A ticket description is required.")

        if not self.github.is_configured():
            return TicketResult(
                False,
                "Support ticketing is not configured on the server "
                "(missing GitHub credentials). Please contact "
                f"{settings.company_email} or call {settings.company_phone}.",
            )

        body = self._build_body(user_name.strip(), user_email.strip(), description.strip())

        try:
            issue = self.github.create_issue(
                title=title.strip(),
                body=body,
                labels=["support", "customer"],
            )
        except GitHubError as exc:
            logger.error("Ticket creation failed: %s", exc)
            return TicketResult(
                False,
                f"We could not create the support ticket automatically: {exc}. "
                f"Please email {settings.company_email} or call "
                f"{settings.company_phone}.",
            )

        return TicketResult(
            success=True,
            message=(
                f"Support ticket #{issue.number} created successfully. "
                f"Our team will follow up via {user_email.strip()}."
            ),
            url=issue.url,
            number=issue.number,
        )
