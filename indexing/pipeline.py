from pathlib import Path
from indexing.chunker  import chunk_markdown
from indexing.embedder import embed_texts
from indexing.writer   import upsert_chunks

def run_indexing(file_path: Path):
    print(f"Indexing {file_path}...")
    
    chunks = chunk_markdown(Path(file_path)) # step 1
    contents = [chunk["content"] for chunk in chunks] # extract content strings
    embeddings = embed_texts(contents) # step 2
    
    upsert_chunks(chunks, embeddings) # step 3
    
    print("Done.")