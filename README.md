# API-Doc-RAG

A retrieval-augmented generation (RAG) system that answers questions about API documentation with source attribution. Built with Python FastAPI backend, Next.js frontend, Ollama LLMs, and ChromaDB vector storage.

## Features

- **Hybrid Search**: Combines dense vector search (embeddings) and BM25 full-text search via RRF fusion for better relevance
- **Source Attribution**: Every answer includes clickable links to source sections in the docs
- **Interactive Docs Page**: Full API reference rendered from markdown with embedded RAG chat assistant
- **WebSocket Chat**: Real-time conversation interface that maintains chat history per session
- **Structure-Aware Chunking**: Splits markdown docs at H3 headings, preserving code examples and parameter tables as metadata

## Architecture

```
INDEXING (offline)
Markdown Docs → Chunker → Embedder (nomic-embed-text) → ChromaDB

RETRIEVAL + GENERATION (online)
User Query → Embed → Hybrid Search (Dense + BM25) → Rerank → Prompt Assembly → Ollama LLM → Answer + Sources
```

## Project Structure

```
RAG/
├── docs/
│   └── v2/
│       └── api-reference.md          # Source API documentation
├── indexing/
│   ├── chunker.py                    # Markdown → structure-aware chunks
│   ├── embedder.py                   # Vector embeddings via Ollama
│   ├── writer.py                     # Write chunks to ChromaDB
│   └── pipeline.py                   # Orchestrate indexing
├── retrieval/
│   └── retriever.py                  # Hybrid search (dense + BM25)
├── generation/
│   ├── prompt.py                     # Assemble context + prompt
│   └── generator.py                  # Call Ollama LLM + manage history
├── api/                              # Next.js frontend
│   ├── app/                          # Pages & layout
│   ├── components/
│   │   └── chat-widget.jsx           # WebSocket chat modal
│   ├── lib/
│   │   └── docs.js                   # Markdown loader & parser
│   └── package.json
├── config.py                         # Shared settings (models, paths, ports)
├── main.py                           # FastAPI + WebSocket server
├── tester.py                         # Test the RAG pipeline
├── startup.md                        # Backend & frontend startup commands
└── chroma_db/                        # Persisted vector store (auto-created)
```

## Prerequisites

- **Ollama** running locally with models:
  - `nomic-embed-text` (for embeddings)
  - `qwen3` (for chat/generation)
- **Python 3.11+**
- **Node.js 18+** (for frontend)

## Startup

### Backend

From the repo root:

```bash
python main.py
```

Starts FastAPI on `http://localhost:8000` with WebSocket endpoint at `ws://localhost:8000/ws/rag`.

### Frontend

From `api/`:

```bash
npm install
npm run dev
```

Starts Next.js docs page on `http://localhost:3000`.

### Optional: Index New Docs

From the repo root:

```bash
python indexing/pipeline.py
```

Re-indexes `docs/v2/api-reference.md` into ChromaDB. Run this after updating docs.

## Usage

1. Open `http://localhost:3000` in your browser
2. Read the API reference docs
3. Click **Ask AI** button in bottom-right corner
4. Ask a question (e.g., "How do I create a user?")
5. Assistant answers with relevant sections and clickable source links
6. Continue the conversation — history is preserved per session

## Key Design Decisions

- **Asymmetric Embeddings**: `nomic-embed-text` requires prefixes (`search_query:`, `search_document:`) for good similarity scores
- **H3 Chunking**: API docs are split at H3 headings (one endpoint/concept per chunk) to balance specificity and context
- **RRF Fusion**: Dense + BM25 results are combined via Reciprocal Rank Fusion for better coverage
- **Client-Side History**: Chat history is managed by the frontend; backend is stateless
- **Source Navigation**: Clicking a source closes the modal and jumps to the document fragment or opens in a new tab

## Testing

Run the test pipeline:

```bash
python tester.py
```

This retrieves docs for a sample query, generates an answer with history, and displays the result.

## Configuration

Edit `config.py` to change:
- `EMBED_MODEL`: Embedding model name
- `LLM_MODEL`: Generation model name
- `OLLAMA_BASE_URL`: Ollama server endpoint
- `CHUNK_MIN_TOKENS` / `CHUNK_MAX_TOKENS`: Chunk size bounds
- `DOCS_DIR`: Docs folder path

## Performance Notes

- First query may take 5–15 seconds (LLM inference)
- Subsequent queries benefit from query rewriting when history exists
- Vector DB queries are <100ms once the index is built
- Frontend builds instantly with Next.js 16 (Turbopack)# API-Doc-RAG