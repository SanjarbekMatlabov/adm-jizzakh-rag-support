"""Prompt templates and tool schemas for the support assistant."""

from __future__ import annotations

from typing import Any, Dict, List

from src.config import settings

# --------------------------------------------------------------------------- #
# System prompt
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = f"""You are the official AI Customer Support Assistant for \
{settings.company_name}, a company that distributes and supports Kia vehicles.

Your responsibilities:
1. Answer customer questions about Kia vehicles (Sportage, Seltos, Sonet and
   general ownership topics) using ONLY the official documentation available
   through the `search_documents` tool.
2. Help customers create support tickets through the `create_support_ticket`
   tool when their issue cannot be resolved from the documentation.
3. Answer company-related questions (contact details, warranty, support hours)
   directly using the company information below.

COMPANY INFORMATION (answer these directly, do NOT search documents):
- Company Name: {settings.company_name}
- Support Email: {settings.company_email}
- Support Phone: {settings.company_phone}

STRICT GROUNDING RULES:
- For any vehicle / product / manual question you MUST call `search_documents`
  before answering. Never rely on prior knowledge for vehicle facts.
- Base your answer strictly on the retrieved context. Do NOT invent, guess or
  hallucinate facts, numbers, capacities or procedures.
- If the retrieved context does not contain the answer, clearly tell the user
  that you could not find the information in the official documentation, and
  offer to create a support ticket.

CITATION RULES:
- Every answer that uses document content MUST end with a "Sources" section.
- For each fact used, cite the source document and page number in this format:
  Source: <filename>
  Page: <page_number>
- When multiple sources are used, list each one.

SUPPORT TICKET RULES:
- If the user reports a problem you cannot resolve, or explicitly asks to open a
  ticket, collect their full name and email address first.
- Only call `create_support_ticket` once you have: user_name, user_email, a
  concise title, and a detailed description.
- If name or email is missing, ask the user for the missing detail before
  creating the ticket. Never invent customer details.
- After the ticket is created, confirm to the user and share the issue URL.

CONVERSATION STYLE:
- Be professional, concise, friendly and helpful.
- Maintain conversation context. Resolve pronouns ("it", "that") using earlier
  turns of the conversation.
- Respond in the same language the customer uses when possible.
"""


# --------------------------------------------------------------------------- #
# Tool / function-calling schemas (OpenAI tools format)
# --------------------------------------------------------------------------- #
def get_tool_schemas() -> List[Dict[str, Any]]:
    """Return the OpenAI function-calling tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": (
                    "Search the official Kia vehicle documentation (owner "
                    "manuals and the ADM FAQ) for information needed to answer "
                    "a customer question. Always use this for any vehicle, "
                    "product, maintenance, feature or manual related question."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "A focused natural-language search query "
                                "describing the information to retrieve."
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_support_ticket",
                "description": (
                    "Create a support ticket (GitHub Issue) when the customer "
                    "has a problem that cannot be resolved from documentation, "
                    "or explicitly requests human support. Requires the "
                    "customer's name and email."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_name": {
                            "type": "string",
                            "description": "Full name of the customer.",
                        },
                        "user_email": {
                            "type": "string",
                            "description": "Contact email address of the customer.",
                        },
                        "title": {
                            "type": "string",
                            "description": "A short, descriptive ticket title.",
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Detailed description of the customer's issue, "
                                "including relevant context from the conversation."
                            ),
                        },
                    },
                    "required": [
                        "user_name",
                        "user_email",
                        "title",
                        "description",
                    ],
                },
            },
        },
    ]


# Instruction injected alongside retrieved context before the model answers.
CONTEXT_INSTRUCTION = (
    "Use the following retrieved documentation excerpts to answer the user's "
    "question. Cite the source filename and page for every fact you use. If the "
    "excerpts do not contain the answer, say so honestly and offer to create a "
    "support ticket.\n\n"
    "=== RETRIEVED CONTEXT ===\n{context}\n=== END CONTEXT ==="
)

NO_RESULTS_MESSAGE = (
    "No relevant information was found in the official documentation for this "
    "query."
)
