# Knowledge Base Documents

Place the official documentation PDFs in this folder. The application loads
**every** `*.pdf` file here automatically at startup.

Required documents:

| File | Description |
|------|-------------|
| `Kia_Sportage_2024_Owner_Manual.pdf` | Primary knowledge source (~586 pages) |
| `Kia_Seltos_Owner_Manual.pdf` | Kia Seltos owner manual |
| `Kia_Sonet_Owner_Manual.pdf` | Kia Sonet owner manual |
| `ADM_FAQ.pdf` | Custom ADM Jizzakh FAQ (warranty, service, support, company info) |

Notes:
- At least **3 documents**, **2+ PDFs**, and **1 document exceeding 400 pages**.
- To expand the knowledge base, simply drop additional PDFs here and rebuild
  the index (`python build_index.py --rebuild`).
- `source` (filename) and `page` metadata are preserved for every chunk so
  citations remain accurate.
