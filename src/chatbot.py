"""Conversation orchestrator.

Drives the OpenAI chat completion loop with function calling, maintains
multi-turn memory, executes tools, and returns grounded answers with citations.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI, OpenAIError

from src.config import settings
from src.prompts import SYSTEM_PROMPT, get_tool_schemas
from src.rag import RAGEngine, RetrievalResult
from src.tools import ToolExecutor

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6


@dataclass
class ChatResponse:
    """A single assistant response surfaced to the UI."""

    answer: str
    citations: List[Dict[str, str]] = field(default_factory=list)
    ticket_url: Optional[str] = None
    error: bool = False


class SupportChatbot:
    """Main chatbot engine with RAG + function calling + memory."""

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        tool_executor: Optional[ToolExecutor] = None,
    ) -> None:
        settings.validate_openai()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.chat_model
        self.rag = rag_engine or RAGEngine()
        self.tools = tool_executor or ToolExecutor(rag_engine=self.rag)
        self.tool_schemas = get_tool_schemas()
        # Conversation memory: list of OpenAI-format message dicts.
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def initialize(self, force_rebuild: bool = False) -> None:
        """Prepare the RAG index before serving chat."""
        self.rag.initialize(force_rebuild=force_rebuild)

    def reset(self) -> None:
        """Clear conversation memory (keep the system prompt)."""
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ------------------------------------------------------------------ #
    # Core chat loop
    # ------------------------------------------------------------------ #
    def chat(self, user_message: str) -> ChatResponse:
        """Process one user turn and return the assistant's grounded answer."""
        if not user_message or not user_message.strip():
            return ChatResponse(answer="Please enter a question.", error=True)

        self.history.append({"role": "user", "content": user_message.strip()})

        # Reset per-turn tool state.
        self.tools.last_retrieval = None
        self.tools.last_ticket_url = None

        try:
            answer = self._run_tool_loop()
        except OpenAIError as exc:
            logger.error("OpenAI API error: %s", exc)
            return ChatResponse(
                answer=(
                    "I'm having trouble reaching the AI service right now. "
                    "Please try again in a moment."
                ),
                error=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error during chat.")
            return ChatResponse(
                answer=f"An unexpected error occurred: {exc}",
                error=True,
            )

        citations = self._collect_citations()
        return ChatResponse(
            answer=answer,
            citations=citations,
            ticket_url=self.tools.last_ticket_url,
        )

    def _run_tool_loop(self) -> str:
        """Run the model<->tool loop until a final text answer is produced."""
        for iteration in range(MAX_TOOL_ITERATIONS):
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                tools=self.tool_schemas,
                tool_choice="auto",
                temperature=settings.temperature,
            )
            message = completion.choices[0].message

            # Append the assistant message (with any tool calls) to history.
            assistant_entry: Dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.history.append(assistant_entry)

            # No tool calls => we have a final answer.
            if not message.tool_calls:
                return message.content or ""

            # Execute every requested tool and feed results back.
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                arguments = self._parse_arguments(tool_call.function.arguments)
                result = self.tools.dispatch(name, arguments)
                self.history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": result,
                    }
                )

        logger.warning("Reached max tool iterations without a final answer.")
        return (
            "I wasn't able to fully complete that request. Please rephrase or "
            "contact support directly."
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_arguments(raw: str) -> Dict[str, Any]:
        """Safely parse JSON tool arguments from the model."""
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse tool arguments: %s", raw)
            return {}

    def _collect_citations(self) -> List[Dict[str, str]]:
        """Return citations from the most recent retrieval, if any."""
        retrieval: Optional[RetrievalResult] = self.tools.last_retrieval
        if not retrieval or not retrieval.found:
            return []
        return [
            {"source": c.source, "page": c.page} for c in retrieval.citations
        ]
