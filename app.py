"""Streamlit entry point for the ADM Jizzakh Kia Customer Support AI Assistant.

Enterprise-style chat UI featuring company branding, multi-turn chat history,
source citations, GitHub-backed support tickets and a sidebar info panel.
"""

from __future__ import annotations

import logging

import streamlit as st

from src.chatbot import SupportChatbot
from src.config import configure_logging, settings

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title=f"{settings.company_name} | Kia Support Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main-header {
        background: linear-gradient(90deg, #05141f 0%, #0b2a43 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        color: #ffffff;
    }
    .main-header h1 { margin: 0; font-size: 1.6rem; }
    .main-header p { margin: 0.25rem 0 0 0; opacity: 0.85; font-size: 0.95rem; }
    .citation-box {
        background-color: #f1f5f9;
        border-left: 4px solid #0b2a43;
        padding: 0.5rem 0.9rem;
        margin-top: 0.5rem;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #1e293b;
    }
    .ticket-box {
        background-color: #ecfdf5;
        border-left: 4px solid #059669;
        padding: 0.6rem 0.9rem;
        margin-top: 0.5rem;
        border-radius: 6px;
        font-size: 0.9rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Resource initialization (cached across reruns)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def load_chatbot() -> SupportChatbot:
    """Create and initialize the chatbot once per session/server."""
    bot = SupportChatbot()
    bot.initialize(force_rebuild=settings.rebuild_index)
    return bot


def render_header() -> None:
    """Render the branded header section."""
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if settings.logo_path.exists():
            st.image(str(settings.logo_path), width=90)
        else:
            st.markdown("## 🚗")
    with col_title:
        st.markdown(
            f"""
            <div class="main-header">
                <h1>{settings.company_name} — Kia Customer Support</h1>
                <p>AI assistant for Kia Sportage, Seltos &amp; Sonet owners.
                Answers are grounded in official documentation with source
                citations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    """Render the sidebar information and controls panel."""
    with st.sidebar:
        st.header("ℹ️ About")
        st.write(
            "This assistant answers Kia ownership questions using official "
            "manuals and the ADM FAQ. If it can't find an answer, it can open "
            "a support ticket for you."
        )

        st.divider()
        st.subheader("📞 Contact")
        st.markdown(
            f"""
            - **Company:** {settings.company_name}
            - **Email:** {settings.company_email}
            - **Phone:** {settings.company_phone}
            """
        )

        st.divider()
        st.subheader("📚 Knowledge Base")
        pdfs = sorted(settings.data_dir.glob("*.pdf"))
        if pdfs:
            for pdf in pdfs:
                st.markdown(f"- `{pdf.name}`")
        else:
            st.warning("No PDF documents found in the data directory.")

        st.divider()
        st.subheader("🔧 System Status")
        st.markdown(
            f"- OpenAI key: {'✅' if settings.openai_api_key else '❌ missing'}"
        )
        st.markdown(
            "- GitHub tickets: "
            f"{'✅ enabled' if settings.github_configured() else '⚠️ disabled'}"
        )

        st.divider()
        st.subheader("💡 Example Questions")
        st.markdown(
            """
            - How do I connect Apple CarPlay?
            - What engine oil should I use?
            - What is the fuel tank capacity?
            - When should brake fluid be replaced?
            - What does the check engine light mean?
            """
        )

        st.divider()
        if st.button("🧹 Clear conversation", use_container_width=True):
            st.session_state.messages = []
            if "chatbot" in st.session_state:
                st.session_state.chatbot.reset()
            st.rerun()


def render_citations(citations: list[dict]) -> None:
    """Render a citation block under an assistant message."""
    if not citations:
        return
    lines = "".join(
        f"<div>📄 <strong>{c['source']}</strong> — page {c['page']}</div>"
        for c in citations
    )
    st.markdown(f'<div class="citation-box">{lines}</div>', unsafe_allow_html=True)


def render_ticket(url: str) -> None:
    """Render a created-ticket confirmation block."""
    st.markdown(
        f'<div class="ticket-box">🎫 <strong>Support ticket created.</strong> '
        f'<a href="{url}" target="_blank">View ticket</a></div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application main loop."""
    render_header()
    render_sidebar()

    # --- Guard: configuration ---------------------------------------- #
    if not settings.openai_api_key:
        st.error(
            "⚠️ OPENAI_API_KEY is not configured. Set it in your environment "
            "(or HuggingFace Space secrets) to start the assistant."
        )
        st.stop()

    # --- Initialize chatbot ------------------------------------------ #
    try:
        if "chatbot" not in st.session_state:
            with st.spinner("Preparing knowledge base and assistant..."):
                st.session_state.chatbot = load_chatbot()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to initialize chatbot.")
        st.error(f"Failed to initialize the assistant: {exc}")
        st.stop()

    chatbot: SupportChatbot = st.session_state.chatbot

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Render existing chat history -------------------------------- #
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_citations(msg.get("citations", []))
                if msg.get("ticket_url"):
                    render_ticket(msg["ticket_url"])

    # --- Handle new input -------------------------------------------- #
    prompt = st.chat_input("Ask about your Kia vehicle...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.chat(prompt)
            st.markdown(response.answer)
            render_citations(response.citations)
            if response.ticket_url:
                render_ticket(response.ticket_url)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response.answer,
                "citations": response.citations,
                "ticket_url": response.ticket_url,
            }
        )


if __name__ == "__main__":
    main()
