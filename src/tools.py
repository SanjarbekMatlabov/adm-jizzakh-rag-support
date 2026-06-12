"""Function-calling tool dispatch layer.

Maps the OpenAI tool names to concrete implementations (RAG search and support
ticket creation) and returns JSON-serializable results for the model.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from src.rag import RAGEngine, RetrievalResult
from src.ticket_tool import SupportTicketService

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes the tools requested by the model during function calling."""

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        ticket_service: Optional[SupportTicketService] = None,
    ) -> None:
        self.rag = rag_engine or RAGEngine()
        self.tickets = ticket_service or SupportTicketService()
        # Track the most recent retrieval so the UI can render citations.
        self.last_retrieval: Optional[RetrievalResult] = None
        self.last_ticket_url: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Individual tools
    # ------------------------------------------------------------------ #
    def search_documents(self, query: str) -> str:
        """Tool: retrieve relevant documentation for a query."""
        logger.info("Tool call: search_documents(query=%r)", query)
        result = self.rag.search(query)
        self.last_retrieval = result
        payload = {
            "found": result.found,
            "context": result.context,
            "citations": [
                {"source": c.source, "page": c.page} for c in result.citations
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    def create_support_ticket(
        self,
        user_name: str,
        user_email: str,
        title: str,
        description: str,
    ) -> str:
        """Tool: create a support ticket as a GitHub issue."""
        logger.info("Tool call: create_support_ticket(title=%r)", title)
        result = self.tickets.create_ticket(
            user_name=user_name,
            user_email=user_email,
            title=title,
            description=description,
        )
        if result.success and result.url:
            self.last_ticket_url = result.url
        payload = {
            "success": result.success,
            "message": result.message,
            "issue_url": result.url,
            "issue_number": result.number,
        }
        return json.dumps(payload, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # Dispatch
    # ------------------------------------------------------------------ #
    def dispatch(self, name: str, arguments: Dict[str, Any]) -> str:
        """Route a tool call by name to the matching implementation."""
        try:
            if name == "search_documents":
                return self.search_documents(query=arguments.get("query", ""))
            if name == "create_support_ticket":
                return self.create_support_ticket(
                    user_name=arguments.get("user_name", ""),
                    user_email=arguments.get("user_email", ""),
                    title=arguments.get("title", ""),
                    description=arguments.get("description", ""),
                )
        except Exception as exc:  # noqa: BLE001 - never crash the chat loop
            logger.exception("Tool '%s' raised an error.", name)
            return json.dumps({"error": f"Tool execution failed: {exc}"})

        logger.warning("Unknown tool requested: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})
