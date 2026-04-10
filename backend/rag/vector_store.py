import json
import os
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from rag.embeddings import get_embedding
from rag.ingest import INDEX_PATH, METADATA_PATH, build_index

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_STORE = None


def load_store() -> dict:
    global _STORE
    if _STORE is not None:
        return _STORE

    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        _STORE = build_index()
        return _STORE

    index = faiss.read_index(str(INDEX_PATH))
    chunks = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    _STORE = {
        "index": index,
        "chunks": chunks,
    }
    return _STORE


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    store = load_store()
    query_embedding = np.array([get_embedding(query)], dtype="float32")
    faiss.normalize_L2(query_embedding)

    distances, indices = store["index"].search(query_embedding, top_k)
    results = []

    for rank, chunk_index in enumerate(indices[0]):
        if chunk_index < 0:
            continue
        chunk = store["chunks"][chunk_index]
        results.append(
            {
                **chunk,
                "score": float(distances[0][rank]),
            }
        )

    return results


def generate_grounded_answer(query: str, retrieved_docs: list[dict]) -> str:
    context_blocks = [
        f"Source: {doc['title']}\nContent: {doc['content']}"
        for doc in retrieved_docs
    ]
    context = "\n\n".join(context_blocks)

    response = client.responses.create(
        model=CHAT_MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You are an IT support assistant for Constellations School. "
                    "Answer only with the provided context. "
                    "If the context is not enough, say that the request should be escalated."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nContext:\n{context}",
            },
        ],
    )
    return response.output_text.strip()


def search(query: str, top_k: int = 3) -> dict:
    retrieved_docs = retrieve(query, top_k=top_k)
    answer = generate_grounded_answer(query, retrieved_docs)
    return {
        "answer": answer,
        "sources": [doc["title"] for doc in retrieved_docs],
        "documents": retrieved_docs,
    }
