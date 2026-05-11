# from pathlib import Path
# from indexing.chunker import chunk_markdown
# from indexing.embedder import embed_texts

# chunks = chunk_markdown(Path("v2/api-reference.md"))

# # for c in chunks:
# #     print("─" * 50)
# #     print("ID:      ", c["metadata"]["chunk_id"])
# #     print("Section: ", c["metadata"]["section"])
# #     print("Parent:  ", c["metadata"]["parent_section"])
# #     print("Type:    ", c["metadata"]["chunk_type"])
# #     print("Content: ", c["content"][:80], "...")
# #     print("HasCode: ", bool(c["metadata"]["code_example"]))
# #     print("HasTable:", bool(c["metadata"]["parameter_table"]))

# # embedded_text = embed_text("call ollama to get vector for this text")
# # print(embedded_text)

# contents = [chunk["content"] for chunk in chunks]
# embedded_chunks = embed_texts(contents)

# # print("Vector dims:", len(embedded_chunks[0]))
# # print("First 5 values:", embedded_chunks[0][:5])

# ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
# vectors = embedded_chunks
# metadatas = [chunk["metadata"] for chunk in chunks]
# documents = [chunk["content"] for chunk in chunks]

# from indexing.pipeline import run_indexing
# from pathlib import Path

# run_indexing(Path('v2/api-reference.md'))

# from retrieval.retriever import retrieve
# results = retrieve('how do I create a user?')
# for r in results:
#     print(r['score'], r['metadata']['section'])

# from retrieval.retriever import retrieve
# from generation.prompt import build_prompt

# results = retrieve("how do I create a user?")
# messages = build_prompt("how do I create a user?", results)

# print(messages[0]["content"])  # system prompt
# print("---")
# print(messages[1]["content"])  # user prompt with context

# test_generate.py
from retrieval.retriever import retrieve
from generation.generator import generate_answer

query   = "how do I create a user?"
results = retrieve(query)
answer, history, sources = generate_answer(query, results)

print("Q:", query)
print("A:", answer)
print()

# test follow-up with history
query2   = "what parameters does it accept?"
results2 = retrieve(query2)
answer2, history, sources2 = generate_answer(query2, results2, history)

print("Q:", query2)
print("A:", answer2)

# from retrieval.retriever import retrieve
# results = retrieve("What parameters does the /v2/users endpoint accept when creating a user, including required fields like email, name, and role, as well as optional parameters like metadata?")
# for r in results:
#     print(r['score'], r['metadata']['section'])