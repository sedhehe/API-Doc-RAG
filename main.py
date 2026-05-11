import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from generation.generator import generate_answer


app = FastAPI(title="RAG WebSocket")


def normalize_history(raw_history: object) -> list[dict]:
	if not isinstance(raw_history, list):
		return []

	history: list[dict] = []
	for item in raw_history:
		if not isinstance(item, dict):
			continue

		role = item.get("role")
		content = item.get("content")
		if role in {"system", "user", "assistant"} and content is not None:
			history.append({"role": role, "content": str(content)})

	return history


@app.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}


@app.websocket("/ws/rag")
async def rag_websocket(websocket: WebSocket) -> None:
	await websocket.accept()
	history: list[dict] = []

	try:
		while True:
			raw_message = await websocket.receive_text()

			try:
				payload = json.loads(raw_message)
			except json.JSONDecodeError:
				payload = {"query": raw_message}

			if isinstance(payload, dict) and payload.get("type") == "reset":
				history = []
				await websocket.send_json({"type": "reset", "history": history})
				continue

			query = ""
			if isinstance(payload, dict):
				query = str(payload.get("query", "")).strip()

			if not query:
				await websocket.send_json(
					{"type": "error", "message": "A query is required."}
				)
				continue

			incoming_history = normalize_history(payload.get("history")) if isinstance(payload, dict) else []
			active_history = incoming_history or history

			answer, updated_history, sources = generate_answer(query=query, results=[], history=active_history)
			history = updated_history

			await websocket.send_json(
				{
					"type": "answer",
					"query": query,
					"answer": answer,
					"history": history,
					"sources": sources,
				}
			)

	except WebSocketDisconnect:
		return
	except Exception as exc:
		await websocket.send_json({"type": "error", "message": str(exc)})


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
