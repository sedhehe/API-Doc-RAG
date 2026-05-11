def reorder_for_lost_middle(results: list[dict]) -> list[dict]:
    if len(results) <= 2:
        return results
    return [results[0], results[2], results[1]]

def build_context_block(results: list[dict]) -> str:
    reordered = reorder_for_lost_middle(results)
    blocks = []

    for i, result in enumerate(reordered):
        meta = result["metadata"]
        
        header  = f"[Source {i+1} | {meta['section']} | {meta['parent_section']} | {meta['source_url']}]"
        body    = result["content"]
        code    = f"Example:\n{meta['code_example']}" if meta['code_example'] else ""

        block   = f"{header}\n{body}\n{code}"
        blocks.append(block)
        
    return "\n\n".join(blocks)

SYSTEM_PROMPT = """You are an API documentation assistant.
Answer questions using ONLY the provided documentation context.
Rules:
- If the answer is not in the context, say "I couldn't find that in the documentation."
- Always cite which source section your answer comes from.
- Keep answers concise and technical.
- If a code example exists in the context, include it.
- Never answer from general knowledge."""

def build_prompt(query: str, results: list[dict]) -> list[dict]:
    context = build_context_block(results)
    
    USER_PROMPT = f"""Documentation Context:
{context}

Question: {query}"""
    
    return [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": USER_PROMPT}
    ]