from pathlib import Path

DOCS_DIR = Path("docs")
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen3"
REWRITE_MODEL = "qwen3:0.6b"
CHUNK_MIN_TOKENS = 30 # ignore chunks smaller than this
CHUNK_MAX_TOKENS = 400 # split chunks larger than this
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "api_docs"
