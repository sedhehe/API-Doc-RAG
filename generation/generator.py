import ollama

from config import LLM_MODEL, OLLAMA_BASE_URL
from generation.prompt import build_prompt
from retrieval.retriever import retrieve


client = ollama.Client(host=OLLAMA_BASE_URL)

def rewrite_query(query: str, history: list[dict]) -> str:
    if not history:
        return query
    
    # ask the LLM to rewrite the query using conversation context
    messages = [
        {
            "role": "system",
            "content": """Rewrite the user's question to be self-contained using conversation history.
                        Return ONLY a short, keyword-dense search query (max 8 words).
                        No full sentences. No punctuation. Just key terms.
                        Example: 'create user endpoint required parameters'"""
        },
        *history,
        {
            "role": "user", 
            "content": f"Rewrite this question to be self-contained: {query}"
        }
    ]
    
    response = client.chat(model=LLM_MODEL, messages=messages)
    rewritten = response.message.content.strip()
    return rewritten


def generate_answer(
    query:   str,
    results: list[dict],
    history: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    conversation_history = list(history or [])
    
    # rewrite query if there's history
    retrieval_query = rewrite_query(query, conversation_history)
    
    # retrieve with rewritten query
    results = retrieve(retrieval_query)
    
    # generate with original query + history
    messages = build_prompt(query, results)
    final_messages = [messages[0]] + conversation_history + [messages[1]]
    
    response = client.chat(model=LLM_MODEL, messages=final_messages)
    answer   = response.message.content

    updated_history = conversation_history + [
        {"role": "user",      "content": query},
        {"role": "assistant", "content": answer},
    ]

    return answer, updated_history, results