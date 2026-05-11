import ollama
from config import EMBED_MODEL

def embed_text(text: str) -> list[float]:
    # call ollama to get vector for this text
    # return the vector as a list of floats
    
    embedded_text = ollama.embed(model=EMBED_MODEL, input=text)
    return embedded_text.embeddings[0]

def embed_texts(texts: list[str]) -> list[list[float]]:
    prefixed = [f"search_document: {t}" for t in texts]
    response = ollama.embed(model=EMBED_MODEL, input=prefixed)
    return response.embeddings