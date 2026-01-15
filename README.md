# NetSuite Research & Documentation

A comprehensive research platform for NetSuite connector development, featuring vectorized documentation search and RAG-powered Q&A.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

## Features

- **Semantic Search**: Search NetSuite documentation using natural language
- **RAG Chat**: Ask questions and get AI-powered answers with source citations
- **Web Search Integration**: Automatically search the web and vectorize results for future use
- **Research Docs**: Comprehensive documentation on objects, permissions, API limits
- **Vectorization Pipeline**: Process and index NetSuite PDF documentation

---

## Quick Start

### Deploy to Railway

1. Fork this repository
2. Connect to Railway
3. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PINECONE_API_KEY`: Your Pinecone API key
   - `PINECONE_INDEX_NAME`: Index name (default: `netsuite-docs`)
4. Deploy!

### Run Locally

```bash
# Clone the repository
git clone https://github.com/Legolasan/netsuite_research.git
cd netsuite_research

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp vectorization/.env.example .env
# Edit .env with your API keys

# Run the web app
cd webapp
uvicorn main:app --reload
```

Visit `http://localhost:8000` to access the dashboard.

---

## Project Structure

```
netsuite_research/
├── webapp/                     # FastAPI Web Application
│   ├── main.py                # App entry point & routes
│   ├── services/              # Search & Chat services
│   ├── templates/             # Jinja2 HTML templates
│   ├── static/                # CSS/JS assets
│   └── requirements.txt       # Web app dependencies
│
├── vectorization/             # PDF Vectorization Pipeline
│   ├── config.py              # Configuration module
│   ├── extract_pdfs.py        # PDF text extraction
│   ├── chunk_text.py          # Text chunking
│   ├── vectorize_docs.py      # Pinecone vectorization
│   ├── query_docs.py          # Semantic search
│   └── rag_helper.py          # RAG Q&A interface
│
├── 01_objects/                # Object Catalog
├── 02_relations/              # Object Relationships
├── 03_permissions/            # Permissions Matrix
├── 04_replication/            # Replication Methods
├── 05_api_limits/             # API Governance
├── 06_operations/             # API Operations
├── 07_summary/                # Implementation Summary
│
├── Procfile                   # Railway deployment
├── railway.json               # Railway configuration
├── requirements.txt           # Combined dependencies
└── README.md                  # This file
```

---

## Research Documentation

| Document | Description |
|----------|-------------|
| [Objects Catalog](01_objects/objects_catalog.md) | Complete list of 128+ supported objects |
| [Object Relations](02_relations/object_relations.md) | Entity relationships and diagrams |
| [Permissions Matrix](03_permissions/permissions_matrix.md) | Required permissions per object |
| [Replication Methods](04_replication/replication_methods.md) | Incremental vs full load details |
| [API Governance](05_api_limits/api_governance.md) | Rate limits and best practices |
| [Operations Catalog](06_operations/operations_catalog.md) | Available API operations |
| [Implementation Status](07_summary/implementation_status.md) | Current state summary |
| [Improvement Opportunities](07_summary/improvement_opportunities.md) | Prioritized enhancements |

---

## Vectorization Pipeline

Index your NetSuite PDF documentation for semantic search:

```bash
# Navigate to vectorization folder
cd vectorization

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run vectorization
python vectorize_docs.py

# Test search (interactive mode)
python query_docs.py -i

# Test RAG Q&A (interactive mode)
python rag_helper.py -i
```

### Usage Examples

```python
# Semantic search
from query_docs import search_netsuite_docs
results = search_netsuite_docs("What are the API rate limits?")

# RAG Q&A
from rag_helper import ask_netsuite
answer = ask_netsuite("How do I implement incremental sync for Customers?")
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | Yes |
| `PINECONE_API_KEY` | Pinecone API key for vector storage | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | No (default: `netsuite-docs`) |
| `EMBEDDING_MODEL` | OpenAI embedding model | No (default: `text-embedding-3-small`) |
| `TAVILY_API_KEY` | Tavily API key for web search | No (enables live web search) |
| `WEB_CACHE_DAYS` | Days before web content is considered stale | No (default: `7`) |

### Web Search

Web search is powered by [Tavily](https://tavily.com) - an AI-optimized search API. Get your free API key at https://tavily.com (1,000 free searches/month).

When enabled, the app will:
1. Search the web for NetSuite-related content
2. Automatically vectorize and store results in Pinecone
3. Future queries can retrieve cached web knowledge
4. Combine documentation and web results for comprehensive answers

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard home page |
| `/api/search` | POST | Semantic search (supports `include_web` param) |
| `/api/chat` | POST | RAG chat with optional web search |
| `/api/web-search` | POST | Standalone web search with vectorization |
| `/api/refresh-web` | POST | Force fresh web search |
| `/api/web-search-status` | GET | Check web search availability |
| `/api/stats` | GET | Index statistics |
| `/api/categories` | GET | Available categories |
| `/health` | GET | Health check |

---

## Key Findings

### Current Implementation

| Aspect | Status |
|--------|--------|
| Objects Supported | 128+ |
| API Protocol | SOAP (v2022_1) |
| Operations | Read-only (search, getDeleted) |
| Replication | Incremental (Txn/Item) + Full Load |

### Top Improvement Opportunities

| Priority | Improvement | Impact |
|----------|-------------|--------|
| P1 | Enable incremental for Customer/Vendor/Contact | High |
| P1 | SDK upgrade to v2024_1 | Medium |
| P2 | Implement write operations | High |
| P2 | REST API integration | High |
| P3 | SuiteQL support | Medium |

---

## License

Internal use only. Contact the Data Platform team for questions.
