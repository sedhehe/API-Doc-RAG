# Startup Commands

## Backend

From the repo root:

```bash
python main.py
```

This starts the FastAPI server on `http://localhost:8000` with the WebSocket endpoint at `ws://localhost:8000/ws/rag`.

## Frontend

From `api/`:

```bash
npm install
npm run dev
```

This starts the Next.js docs UI on `http://localhost:3000`.

## Prerequisites

- Ollama running locally
- Required models available in Ollama
- ChromaDB persistence already created by the indexing pipeline

## Optional indexing commands

From the repo root:

```bash
python indexing/pipeline.py
```

Use this after doc changes to refresh the vector store.
