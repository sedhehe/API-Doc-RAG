INDEXING
────────
MD / PDF / Web Page
        │
   [Loader + Parser]
        │ ← strip boilerplate, preserve code blocks
        │
   [Structure-Aware Chunker]   ← not naive fixed-size
        │
        ├── Section chunks (prose explanation)
        └── Code chunks (kept whole, tagged)
        │
   [Metadata tagging]
        │  endpoint, method, params, version, chunk_type
        │
   [Embedding model]           ← choice matters here
        │
   [Vector DB + BM25 index]    ← hybrid from day one


RETRIEVAL
─────────
Query → [Query classifier] → [Hybrid search] → [Fast reranker] → [LLM]
                                                      ↑
                                             (this is your latency hotspot)

Good metadata sources:
├── File path / folder structure   → version, category, product area
├── Filename                       → doc type, endpoint group
├── Markdown frontmatter           → author, date, status
├── H1/H2 heading                  → section, topic
└── Regex on content               → endpoint, HTTP method, status codes

Bad metadata sources:
└── Human memory                   → will be forgotten, inconsistent