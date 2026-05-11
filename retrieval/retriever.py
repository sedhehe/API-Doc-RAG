from indexing.embedder import embed_text
from indexing.writer import get_collection
from rank_bm25 import BM25Okapi

def preprocess_query(query: str) -> str:
    # strip filler phrases that add noise
    fillers = [
        "how do i ", "how to ", "what is ", "what are ",
        "can you ", "tell me ", "show me ", "i want to ",
        "how can i ", "where is "
    ]
    cleaned = query.lower().strip()
    for filler in fillers:
        if cleaned.startswith(filler):
            cleaned = cleaned[len(filler):]
            break
    return cleaned

def build_bm25_index(documents: list[str]):
    tokenized = [doc.lower().split() for doc in documents]
    return BM25Okapi(tokenized)

def retrieve(query: str, k: int = 3) -> list[dict]:
    collection = get_collection()
    cleaned    = preprocess_query(query)
    
    # ── DENSE SEARCH ──────────────────────────────
    query_vector = embed_text(f"search_query: {cleaned}")
    dense_results = collection.query(
        query_embeddings = [query_vector],
        n_results = 10,
        include = ["documents", "metadatas", "distances"]
    )
    dense_docs = dense_results["documents"][0]
    dense_metas = dense_results["metadatas"][0]
    dense_scores = dense_results["distances"][0]

    # ── BM25 SEARCH ───────────────────────────────
    everything = collection.get(include=["documents", "metadatas"])
    all_docs = everything["documents"]
    all_metas = everything["metadatas"]
    
    bm25 = build_bm25_index(all_docs)
    bm25_scores = bm25.get_scores(cleaned.lower().split())
    top_bm25_idx = sorted(
        range(len(bm25_scores)),
        key = lambda i: bm25_scores[i],
        reverse = True
    )[:10]

    # ── RRF FUSION ────────────────────────────────
    rrf_scores = {}

    for rank, doc in enumerate(dense_docs):
        chunk_id = dense_metas[rank]["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1/(rank + 60)

    for rank, idx in enumerate(top_bm25_idx):
        chunk_id = all_metas[idx]["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1/(rank + 60)

    # ── BUILD RESULTS ─────────────────────────────
    # map chunk_id → content + metadata for final output
    id_to_doc = {m["chunk_id"]: d for d, m in zip(all_docs,  all_metas)}
    id_to_meta = {m["chunk_id"]: m for m in all_metas}

    top_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:k]

    return [
        {
            "content": id_to_doc[cid],
            "metadata": id_to_meta[cid],
            "score": round(rrf_scores[cid], 4)
        }
        for cid in top_ids
    ]
