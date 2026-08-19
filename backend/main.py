from dataclasses import asdict
from fastapi import FastAPI
from pydantic import BaseModel
from backend.retrieval import agent_invoke


app = FastAPI()

@app.get("/query")
def send_query(query: str, session_id: str | None = None):
    answer, citations, session_id = agent_invoke(query=query, session_id=session_id)
    return {
        "answer": answer,
        "citations": [asdict(c) for c in citations],
        "session_id": session_id,
    }


