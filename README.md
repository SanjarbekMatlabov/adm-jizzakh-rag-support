---
title: ADM Jizzakh Kia Customer Support AI
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.36.0
app_file: app.py
pinned: false
---

# 🚗 ADM Jizzakh — Kia Customer Support AI Assistant

An intelligent, production-ready customer support chatbot for **ADM Jizzakh**
that helps Kia vehicle owners. It answers questions from **official Kia
documentation** using **Retrieval Augmented Generation (RAG)** and
automatically creates **GitHub-backed support tickets** when an answer cannot be
found.

---

## 📋 Project Overview

The assistant grounds every vehicle-related answer in official Kia owner manuals
and the ADM FAQ. It cites the **source document** and **page number** for each
fact, maintains **multi-turn conversation memory**, and uses **OpenAI function
calling** to decide when to search documents or open a support ticket.

Typical questions it handles:

- How do I connect Apple CarPlay?
- What engine oil should I use?
- How do I reset the infotainment system?
- What is the fuel tank capacity?
- What does a warning light mean?
- When should brake fluid be replaced?

---

## 🏗️ Architecture

```
            ┌─────────────────────────┐
            │        Customer         │
            └────────────┬────────────┘
                         │
                 ┌───────▼────────┐
                 │  Streamlit UI  │   branding · chat · citations · tickets
                 └───────┬────────┘
                         │
              ┌──────────▼───────────┐
              │  OpenAI GPT-4o-mini  │   conversation memory + reasoning
              └──────────┬───────────┘
                         │  function calling
        ┌────────────────┴─────────────────┐
        │                                   │
┌───────▼─────────┐               ┌─────────▼──────────┐
│ search_documents│               │create_support_ticket│
└───────┬─────────┘               └─────────┬──────────┘
        │                                   │
   ┌────▼─────┐                       ┌──────▼───────┐
   │  FAISS   │                       │ GitHub Issues│
   └────┬─────┘                       └──────────────┘
        │
┌───────▼────────────┐
│  Kia Manuals + FAQ │  (PyPDFLoader → chunks → text-embedding-3-small)
└────────────────────┘
```

---

## ✨ Features

- **Document-grounded answers** with strict no-hallucination rules.
- **Source citations** (document name + page number) on every answer.
- **Multi-turn conversation memory** with pronoun resolution.
- **OpenAI function calling** — the model decides when to search or open tickets.
- **GitHub Issues integration** for automatic support ticket creation.
- **Company-aware** — answers contact/warranty questions directly.
- **Enterprise Streamlit UI** — branding, chat history, citations, sidebar panel.
- **Robust error handling** — missing keys, invalid PDFs, empty results, API errors.
- **Modular, typed, PEP8-compliant** code with logging.
- **Scalable** — drop new PDFs into `data/` and rebuild the index.

---

## 📁 Folder Structure

```
project/
├── app.py                  # Streamlit application
├── build_index.py          # Offline FAISS index builder
├── make_logo.py            # Generates the placeholder logo
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/                   # Knowledge-base PDFs (you provide these)
│   ├── Kia_Sportage_2024_Owner_Manual.pdf
│   ├── Kia_Seltos_Owner_Manual.pdf
│   ├── Kia_Sonet_Owner_Manual.pdf
│   └── ADM_FAQ.pdf
├── vector_db/              # Persisted FAISS index (generated)
├── assets/
│   └── logo.png
└── src/
    ├── __init__.py
    ├── config.py           # Settings + env handling + logging
    ├── prompts.py          # System prompt + tool schemas
    ├── document_loader.py  # PyPDFLoader + RecursiveCharacterTextSplitter
    ├── embeddings.py       # OpenAI embeddings factory
    ├── vector_store.py     # FAISS build / load / search
    ├── rag.py              # Retrieval + citation assembly
    ├── github_client.py    # GitHub Issues API client
    ├── ticket_tool.py      # Ticket validation + creation
    ├── tools.py            # Function-calling dispatch layer
    ├── chatbot.py          # Chat loop + memory + tool execution
    └── utils.py            # Shared helpers
```

---

## 🛠️ Installation Guide

Requires **Python 3.11+**.

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd project

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🔐 Environment Setup

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `GITHUB_TOKEN` | ⚠️ | GitHub PAT with `repo` scope (for tickets) |
| `GITHUB_REPOSITORY` | ⚠️ | Target repo as `owner/repo` |
| `COMPANY_NAME` | – | Defaults to `ADM Jizzakh` |
| `COMPANY_EMAIL` | – | Defaults to `support@adm.uz` |
| `COMPANY_PHONE` | – | Defaults to `+998551522222` |
| `OPENAI_CHAT_MODEL` | – | Defaults to `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | – | Defaults to `text-embedding-3-small` |

Then add your PDF documents to the `data/` folder (see `data/README.md`).

---

## ▶️ Running Locally

```bash
# (Optional) pre-build the vector index
python build_index.py

# Launch the Streamlit app
streamlit run app.py
```

The app opens at `http://localhost:8501`. On first launch it builds the FAISS
index from the PDFs in `data/` (subsequent launches reuse the persisted index).

To force an index rebuild after adding/updating documents:

```bash
python build_index.py --rebuild
```

---

## 🔗 GitHub Integration

Support tickets are created as **GitHub Issues**:

1. Create a Personal Access Token with the `repo` scope.
2. Set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (`owner/repo`).
3. When the assistant can't answer or the user requests help, it collects the
   customer's name and email, then opens an issue:

```
Title: Unable to Connect Apple CarPlay
Body:
Name: John Doe
Email: john@example.com

Description: Customer cannot connect Apple CarPlay after software update.
```

The created issue URL is returned to the customer in chat.

---

## 🚀 HuggingFace Spaces Deployment

1. Create a new **Streamlit** Space.
2. Push this repository (including `app.py`, `requirements.txt`, `src/`,
   `data/`, `assets/`, and the YAML header at the top of this README).
3. In **Settings → Variables and secrets**, add:
   - `OPENAI_API_KEY`
   - `GITHUB_TOKEN`
   - `GITHUB_REPOSITORY`
   - (optional) `COMPANY_NAME`, `COMPANY_EMAIL`, `COMPANY_PHONE`
4. The Space builds automatically and launches `app.py`. The FAISS index is
   built on first run from the PDFs committed to `data/`.

> Tip: For large manuals, commit a pre-built `vector_db/` index to speed up cold
> starts, or set `REBUILD_INDEX=false` (default) so the persisted index is reused.

---

## 💬 Example Questions

- "How do I connect Apple CarPlay?"
- "What engine oil should I use for the Sportage?"
- "What is the fuel tank capacity?" *(expects a cited answer with page number)*
- "What's your support phone number?" *(answered directly, no search)*
- "My infotainment keeps freezing, please open a ticket." *(ticket workflow)*

---

## 🔮 Future Improvements

- Hybrid search (BM25 + dense) and re-ranking for higher precision.
- Streaming responses for lower perceived latency.
- Multilingual UI (Uzbek / Russian / English) toggle.
- Per-document and per-page deep links in citations.
- Admin dashboard for ticket analytics.
- Automatic ingestion pipeline for new manuals.
- Caching layer for frequent queries.

---

## 📄 License

Provided for ADM Jizzakh. Adapt as needed for your deployment.
#   a d m - j i z z a k h - r a g - s u p p o r t  
 