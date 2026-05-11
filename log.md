# RAG System Build Log
**Project:** API Documentation RAG  
**Stack:** Python · FastAPI · Ollama (Qwen3 + nomic-embed-text) · ChromaDB · Next.js  
**Purpose:** A retrieval-augmented generation system that answers questions about API documentation with source attribution.

---

## Table of Contents
1. [What Is RAG and Why We Built It This Way](#1-what-is-rag)
2. [Architecture Overview](#2-architecture-overview)
3. [The Two Planes](#3-the-two-planes)
4. [Project Structure](#4-project-structure)
5. [Stage 1 — Chunking](#5-stage-1--chunking)
6. [Stage 2 — Embedding](#6-stage-2--embedding)
7. [Stage 3 — Writing to Vector DB](#7-stage-3--writing-to-vector-db)
8. [Stage 4 — Indexing Pipeline](#8-stage-4--indexing-pipeline)
9. [Stage 5 — Retrieval](#9-stage-5--retrieval)
10. [Stage 6 — Hybrid Search](#10-stage-6--hybrid-search)
11. [Stage 7 — Prompt Assembly](#11-stage-7--prompt-assembly)
12. [Stage 8 — Generation](#12-stage-8--generation)
13. [Bugs Found and Fixed](#13-bugs-found-and-fixed)
14. [Key Design Decisions and Tradeoffs](#14-key-design-decisions-and-tradeoffs)
15. [What To Build Next](#15-what-to-build-next)

---

## 1. What Is RAG

**Problem:** LLMs hallucinate when asked about specific, structured information they half-know (like your API docs).

**Solution:** Instead of asking the LLM to remember, give it the relevant information at query time. The LLM's job shifts from *remembering* to *reasoning over provided context*.

**Why this fits API docs:**
- Ground truth is exact — wrong answers are clearly wrong
- High structure (endpoints, params, error codes)
- Lookup/how-to queries are the dominant pattern
- Source attribution builds trust

---

## 2. Architecture Overview

```
INDEXING (offline)
Raw Docs → Chunker → Embedder → Vector DB

RETRIEVAL (online)  
Query → Embed → Hybrid Search → Reorder → Prompt → LLM → Answer + Sources
```

Quality is determined mostly by the **indexing plane**. If the right chunk never gets indexed correctly, no amount of retrieval tuning will fix it.

---

## 3. The Two Planes

### Offline Plane (Indexing)
Runs once (or on doc update). Builds the searchable index.

### Online Plane (Retrieval + Generation)
Runs on every user query. Must be fast.

**The three places quality breaks:**

| Failure | Symptom | Fix |
|---|---|---|
| Indexing | Right answer never retrieved | Fix chunking or metadata |
| Retrieval | Wrong chunks retrieved | Fix embedding, search, reranking |
| Generation | Answer doesn't match chunks | Fix prompt, reduce hallucination |

---

## 4. Project Structure

```
rag-api/
├── docs/
│   └── v2/
│       └── api-reference.md       ← source API docs
├── indexing/
│   ├── __init__.py
│   ├── chunker.py                 ← splits markdown into chunks
│   ├── embedder.py                ← calls Ollama for vectors
│   ├── writer.py                  ← writes to ChromaDB
│   └── pipeline.py                ← wires all three together
├── retrieval/
│   ├── __init__.py
│   └── retriever.py               ← hybrid search (dense + BM25)
├── generation/
│   ├── __init__.py
│   ├── prompt.py                  ← assembles context + prompt
│   └── generator.py               ← calls Ollama LLM
├── api/
│   ├── __init__.py
│   └── routes.py                  ← FastAPI endpoints
├── config.py                      ← all settings in one place
└── main.py                        ← entry point
```

**Why this structure:** Each folder = one stage of the pipeline. When something breaks, you know exactly which file to look at.

---

## 5. Stage 1 — Chunking

**File:** `indexing/chunker.py`

### What it does
Reads a Markdown file line by line and splits it into self-contained chunks.

### Chunk unit
**H3 heading + prose paragraph(s)** = one chunk.

Why H3? API docs are structured as H1 (doc title) → H2 (section) → H3 (endpoint/concept). H3 is the atomic unit — one coherent idea.

### What goes where

| Part | Goes into | Why |
|---|---|---|
| H3 heading + prose | `chunk["content"]` | Gets embedded — matches natural language queries |
| Parameter tables | `chunk["metadata"]["parameter_table"]` | Stored but not embedded — tables are noisy for vectors |
| Code examples | `chunk["metadata"]["code_example"]` | Stored, attached at render time |
| H2 heading | `chunk["metadata"]["parent_section"]` | Context, not content |

### Metadata schema (all auto-derived)

```python
{
    "version":         # from folder path e.g. "v2"
    "doc_category":    # from filename e.g. "api_reference"
    "doc_title":       # from H1
    "parent_section":  # from H2
    "section":         # from H3
    "chunk_type":      # "endpoint" or "concept"
    "code_example":    # extracted code blocks
    "parameter_table": # extracted tables
    "chunk_id":        # deterministic slug e.g. "v2-users-create-user"
    "source_url":      # "/docs/v2/api_reference#create-user"
    "source_file":     # "v2/api-reference.md"
}
```

### Why deterministic chunk_id
```
Random ID:       re-index → duplicate chunks in DB ❌
Deterministic:   re-index → updates existing chunk ✅
```

Built from: `f"{version}-{slugify(h2)}-{slugify(h3)}"`

### Key chunking rules

**Guard condition:**
```python
if not current_h3 or (not prose_lines and not table and not code):
    return
```
Save chunk only if heading exists AND at least one of prose/table/code is present.

**Content fallback:**
```python
content_text = prose if prose else table
```
If no prose exists (e.g. error code tables), use the table as embeddable content. Without this, sections like `## Errors` were completely invisible to retrieval.

**Tracking state while reading line by line:**
```python
current_h2    # updates on ## lines → parent_section
current_h3    # updates on ### lines → chunk boundary
inside_code   # toggles on ``` lines
prose_lines   # accumulates until next heading
```

### Path-based version extraction
```python
parts   = file_path.parts
version = parts[-2]   # always second-to-last
```
Use negative indexing — the structure before the version can change, but version and filename are always at the end.

---

## 6. Stage 2 — Embedding

**File:** `indexing/embedder.py`  
**Model:** `nomic-embed-text` via Ollama  
**Output:** 768-dimensional vectors

### Two functions

```python
def embed_text(text: str) -> list[float]:
    # single text → single vector (used for queries)

def embed_texts(texts: list[str]) -> list[list[float]]:
    # batch of texts → batch of vectors (used for indexing)
```

Ollama supports batch embedding in one call: `ollama.embed(model=..., input=[a, b, c])`. Use this for indexing — avoids 19 separate HTTP calls.

### Asymmetric prefixes — critical

`nomic-embed-text` is an asymmetric model. Without prefixes, query and document vectors land in a generic space and similarity scores are low (0.3).

```python
# at index time (documents)
f"search_document: {text}"

# at query time
f"search_query: {query}"
```

With prefixes, cosine similarity scores jump to 0.6+.

### What NOT to embed
- Parameter tables → noisy for vectors
- Code blocks → syntactically dense, poor semantic match with natural language queries
- Metadata fields → not searchable content

---

## 7. Stage 3 — Writing to Vector DB

**File:** `indexing/writer.py`  
**Database:** ChromaDB (local, persistent)

### Collection setup

```python
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}   # critical
)
```

**Why cosine, not default L2:**  
ChromaDB defaults to L2 (Euclidean) distance. `1 - L2_distance` does not give meaningful similarity. Cosine similarity is what you want for semantic search. Setting this wrong gives misleadingly low scores.

### Upsert, not insert

```python
collection.upsert(
    ids        = ids,          # deterministic chunk_ids
    embeddings = embeddings,
    metadatas  = metadatas,
    documents  = documents     # raw text content
)
```

Upsert = insert if new, update if exists. Using deterministic chunk_ids means re-indexing updates chunks, not duplicates them.

### Four things stored per chunk

| Field | Content |
|---|---|
| `id` | deterministic chunk_id |
| `embedding` | 768d vector |
| `metadata` | all metadata fields |
| `document` | raw text (H3 + prose) |

---

## 8. Stage 4 — Indexing Pipeline

**File:** `indexing/pipeline.py`

Wires the three stages together:

```python
def run_indexing(file_path: Path):
    chunks     = chunk_markdown(file_path)           # stage 1
    contents   = [c["content"] for c in chunks]
    embeddings = embed_texts(contents)               # stage 2
    upsert_chunks(chunks, embeddings)                # stage 3
```

Run this whenever docs change. For v1, a full re-index on every deploy is fine.

---

## 9. Stage 5 — Retrieval

**File:** `retrieval/retriever.py`

### Query preprocessing

```python
def preprocess_query(query: str) -> str:
    fillers = ["how do i ", "how to ", "what is ", ...]
    # strips filler phrases from the start of the query
```

"how do I create a user?" → "create a user?"

Filler words dilute the embedding signal. Stripping them improves retrieval precision.

### Dense search

1. Embed cleaned query with `search_query:` prefix
2. Query ChromaDB for top 10 by cosine similarity
3. Returns chunks ordered by vector similarity

### Similarity threshold (important)

Always filter results below a minimum score:
```python
results = [r for r in results if r["score"] >= 0.75]
```
Returning weakly-related chunks leads to hallucination. Saying "I couldn't find that" is better than a confidently wrong answer.

---

## 10. Stage 6 — Hybrid Search

**Why pure dense search isn't enough:**  
Short chunks + one overlapping word can cause wrong rankings. Example: "Add Team Member" contains "user" → ranked above "Create User" for query "how do I create a user?".

**Solution: combine dense (meaning) + BM25 (keywords)**

```
Dense:  finds semantic meaning       → good for concepts
BM25:   finds exact keyword matches  → good for "create", "403", "POST /users"
RRF:    combines both rankings       → best of both
```

### BM25

```python
from rank_bm25 import BM25Okapi

def build_bm25_index(documents: list[str]):
    tokenized = [doc.lower().split() for doc in documents]
    return BM25Okapi(tokenized)

# score query against all docs
bm25_scores = bm25.get_scores(cleaned.lower().split())
```

Must tokenize query the same way as documents (lowercase + split).

### RRF Fusion (Reciprocal Rank Fusion)

```python
rrf_score = 1/(rank + 60)
```

Chunks appearing in both dense and BM25 results get two additions → naturally ranked higher. The constant 60 prevents rank 0 from dominating too heavily.

```
# example
Create User: dense_rank=2 + bm25_rank=1 = 0.016 + 0.016 = 0.032  ✅
Add Team Member: dense_rank=1 + bm25_rank=8 = 0.016 + 0.014 = 0.030
```

**Result after hybrid search:**
```
Before: Add Team Member #1, Create User #2  ❌
After:  Create User #1                      ✅
```

---

## 11. Stage 7 — Prompt Assembly

**File:** `generation/prompt.py`

### Three zones

```
SYSTEM PROMPT  → who the LLM is + behavioral rules
CONTEXT BLOCK  → retrieved chunks, clearly labeled
USER QUERY     → the actual question
```

### Lost middle problem fix

LLMs attend strongly to the beginning and end of context, less to the middle. Fix by reordering 3 chunks:

```python
def reorder_for_lost_middle(results):
    # [best, second, third] → [best, third, second]
    return [results[0], results[2], results[1]]
```

Best chunk at position 1 (high attention), second-best at position 3 (high attention), weakest at position 2 (lost middle).

### Context block format

```
[Source 1 | Create User | Users | /docs/v2/api_reference#create-user]
### Create User
Creates a new user in your workspace...
Example:
response = requests.post(...)
```

Each chunk gets: source label → content → code example (if exists).

### What's included vs excluded from context

| Included | Excluded |
|---|---|
| section, parent_section | chunk_id |
| source_url | version |
| content | doc_title |
| code_example | chunk_type |

### System prompt rules
- Answer using ONLY provided context
- Say "I couldn't find that" if not in context → prevents hallucination
- Always cite source section
- Include code examples if present
- Never use general knowledge

---

## 12. Stage 8 — Generation

**File:** `generation/generator.py`  
**Model:** Qwen3 via Ollama

### Conversational memory

History is passed between turns so the LLM understands follow-up questions:

```python
final_messages = [system_prompt] + history + [current_user_message]
```

History accumulates turn by turn:
```python
updated_history = history + [
    {"role": "user",      "content": query},
    {"role": "assistant", "content": answer}
]
```

### Query rewriting (critical for follow-ups)

**Problem:** "what parameters does it accept?" retrieves wrong chunks because "it" has no meaning to the retriever.

**Fix:** Rewrite the query using history before retrieval:

```python
def rewrite_query(query, history):
    # asks LLM: "rewrite this question to be self-contained"
    # "what parameters does it accept?"
    # → "what parameters does the Create User endpoint accept?"
```

Rewritten query → better retrieval → better answer.

### Full generate_answer flow

```python
def generate_answer(query, results, history=None):
    # 1. rewrite query using history
    retrieval_query = rewrite_query(query, history)
    # 2. retrieve with rewritten query
    results = retrieve(retrieval_query)
    # 3. build prompt with retrieved context
    messages = build_prompt(query, results)
    # 4. inject history between system and user message
    final_messages = [messages[0]] + history + [messages[1]]
    # 5. call LLM
    response = client.chat(model=LLM_MODEL, messages=final_messages)
    # 6. update and return history
    return answer, updated_history
```

---

## 13. Bugs Found and Fixed

### Bug 1: Missing Errors section chunks
**Symptom:** `## Errors` section produced zero chunks.  
**Root cause:** H3s under Errors had no prose — only tables. Guard condition `if not prose_lines: return` skipped them all.  
**Fix:** Changed guard to save chunk if any of prose/table/code exists:
```python
if not current_h3 or (not prose_lines and not table and not code):
    return
```

### Bug 2: Low similarity scores (0.3)
**Symptom:** All retrieval scores below 0.4.  
**Root causes:**  
  A) ChromaDB using L2 distance instead of cosine  
  B) Missing asymmetric prefixes on embeddings  
**Fix:** Added `hnsw:space: cosine` to collection + `search_document:` / `search_query:` prefixes.

### Bug 3: Wrong chunk ranked first
**Symptom:** "Add Team Member" ranked above "Create User" for "how do I create a user?"  
**Root cause:** Word "user" in Add Team Member content caused false similarity. Pure dense search on short text is vulnerable to single-word overlap.  
**Fix:** Implemented hybrid search (dense + BM25 + RRF fusion).

### Bug 4: 403 error query returning wrong results
**Symptom:** "what causes a 403 error?" returned Bearer Token instead of Errors section.  
**Root cause:** Error code tables were stored as metadata, not embedded. Nothing in chunk content to match "403".  
**Fix:** Added content fallback — if no prose, embed the table instead:
```python
content_text = prose if prose else table
```

### Bug 5: Follow-up queries failing
**Symptom:** "what parameters does it accept?" retrieved wrong chunks (HTTP Status Codes, API Key Scopes).  
**Root cause:** Retriever has no access to conversation history. "it" means nothing without context.  
**Fix:** Query rewriting — use LLM to rewrite ambiguous follow-up queries to be self-contained before retrieval.

### Bug 6: Verbose rewritten query dilutes retrieval signal
**Symptom:** Follow-up query rewriting worked but still retrieved wrong chunks.  
**Root cause:** LLM rewrote "what parameters does it accept?" into a full sentence:
```
"What parameters does the /v2/users endpoint accept when creating a user,
including required fields like email, name, and role..."
```
Long verbose queries create a blurry embedding — too many concepts averaged together. BM25 also gets confused by noise words.  
**Fix:** Forced short keyword-dense rewrites in the system prompt:
```python
"Return ONLY a short, keyword-dense search query (max 8 words).
No full sentences. No punctuation. Just key terms.
Example: 'create user endpoint required parameters'"
```
Result: "create user endpoint parameters required optional" → Create User #1 ✅

### Bug 7: Python 3.14 incompatibility
**Symptom:** `pip install chromadb` backtracked through 50+ versions.  
**Root cause:** Python 3.14 too new — no pre-built wheels for ChromaDB's C extensions.  
**Fix:** Used pyenv to switch to Python 3.11.9. Added pyenv init to `~/.zshrc`.

---

## 14. Key Design Decisions and Tradeoffs

### Chunk at H3, not H2
H2 sections are too large → blurry embeddings, noisy retrieval. H3 is one coherent idea.

### Embed prose only, store code/tables as metadata
Keeps vectors semantically clean. Code blocks are syntactically dense and don't match natural language queries. Tables are structured data, not prose.
**Exception:** If no prose exists, use table as content (error code sections).

### Deterministic chunk IDs
Enables upsert on re-index. Random IDs would duplicate chunks on every re-index.

### Hybrid search from day one
Pure dense search fails on short chunks with word overlap. BM25 is free to add and meaningfully improves precision.

### k=3
Enough coverage to handle retrieval misses. Small enough to keep context clean and LLM focused.

### Cosine similarity over L2
L2 distance doesn't map cleanly to `1 - distance` similarity. Cosine is the right metric for semantic similarity in high-dimensional embedding spaces.

### Query rewriting before retrieval
Retriever is stateless — it doesn't know conversation history. Rewriting ambiguous queries makes them self-contained before they hit the retriever.

### Rewritten queries must be short and keyword-dense
Long verbose rewrites create blurry embeddings. Force max 8 words, no filler sentences. The rewrite is for retrieval, not for reading — terseness is a feature.

### History is managed client-side
The server returns updated history with every response. The frontend sends it back with the next request. This keeps the API stateless — no session storage needed on the server.

---

## 15. What To Build Next

### Immediate
- [x] `indexing/chunker.py` ✅
- [x] `indexing/embedder.py` ✅
- [x] `indexing/writer.py` ✅
- [x] `indexing/pipeline.py` ✅
- [x] `retrieval/retriever.py` ✅ hybrid search
- [x] `generation/prompt.py` ✅ lost middle fix
- [x] `generation/generator.py` ✅ query rewriting + history
- [ ] `api/routes.py` — FastAPI REST endpoint
- [ ] `main.py` — server entry point
- [ ] Next.js frontend — WebSocket chat UI with source attribution

### API Design (next step)
One endpoint handles everything:

```
POST /query
Request:  { "query": "...", "history": [] }
Response: { "answer": "...", "sources": [...], "history": [...] }
```

Sources array shape (returned to frontend):
```json
[
  {
    "title":    "Create User",
    "section":  "Users",
    "url":      "/docs/v2/api_reference#create-user"
  }
]
```

History is managed client-side — frontend sends it with each request, backend returns it updated. This keeps the server stateless.

### Quality improvements
- [ ] Similarity threshold filtering (drop results below 0.75)
- [ ] Evaluation dataset — 30-50 question-answer pairs
- [ ] Measure Context Recall@3 across eval set

### Production readiness
- [ ] File hashing for incremental re-indexing (skip unchanged files)
- [ ] Orphan chunk cleanup (delete chunks from deleted sections)
- [ ] Swap ChromaDB → Pinecone or Qdrant
- [ ] Swap Ollama → Gemini API for embeddings + generation
- [ ] Deploy to AWS

### Nice to have
- [ ] Metadata filtering by version in retrieval
- [ ] Reranker for better precision
- [ ] Streaming responses from LLM

---

## Config Reference

```python
# config.py
DOCS_DIR        = Path("docs")
CHROMA_DIR      = Path("chroma_db")
COLLECTION_NAME = "api_docs"
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL     = "nomic-embed-text"
LLM_MODEL       = "qwen3"
```

## Models Reference

| Model | Purpose | Dimensions |
|---|---|---|
| nomic-embed-text | Embeddings | 768 |
| qwen3 | Generation + query rewriting | — |

## Commands Reference

```bash
# setup
pyenv local 3.11.9
python -m venv venv
source venv/bin/activate
pip install chromadb ollama fastapi uvicorn rank-bm25

# pull models
ollama pull nomic-embed-text
ollama pull qwen3

# index docs
python -c "from indexing.pipeline import run_indexing; from pathlib import Path; run_indexing(Path('v2/api-reference.md'))"

# test retrieval
python -c "from retrieval.retriever import retrieve; [print(r['score'], r['metadata']['section']) for r in retrieve('how do I create a user?')]"

# reset index (if changing embedding or chunking)
rm -rf chroma_db
```