import chromadb
from config import CHROMA_DIR, COLLECTION_NAME

def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]):
    collection = get_collection()
    
    ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    
    collection.upsert(
        ids = ids,
        embeddings = embeddings,
        metadatas = metadatas,
        documents = documents
    )
    
    print(f"Upserted {len(ids)} chunks")