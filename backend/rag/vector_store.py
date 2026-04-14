import json
import os
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import KNOWLEDGE_AGENT_PROMPT
from rag.embeddings import get_embedding
from rag.ingest import INDEX_PATH, METADATA_PATH, build_index, current_source_signature

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

    try:
        index = faiss.read_index(str(INDEX_PATH))
        metadata_payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, json.JSONDecodeError):
        _STORE = build_index()
        return _STORE

    if isinstance(metadata_payload, list):
        _STORE = build_index()
        return _STORE

    if metadata_payload.get("source_signature") != current_source_signature():
        _STORE = build_index()
        return _STORE

    chunks = metadata_payload.get("chunks", [])
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


def generate_grounded_answer(query: str, retrieved_docs: list[dict]) -> dict:
    """
    Returns a structured dict with:
      - answer: grounded response text
      - answer_confidence: float 0.0-1.0 (LLM self-assessed)
      - is_password_related: bool
      - reasoning: one sentence about source coverage
    """
    context_blocks = [
        f"Source: {doc['title']}\nContent: {doc['content']}"
        for doc in retrieved_docs
    ]
    context = "\n\n".join(context_blocks)

    response = client.responses.create(
        model=CHAT_MODEL,
        text={"format": {"type": "json_schema", "name": "grounded_answer", "schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "answer_confidence": {"type": "number"},
                "is_password_related": {"type": "boolean"},
                "reasoning": {"type": "string"},
            },
            "required": ["answer", "answer_confidence", "is_password_related", "reasoning"],
            "additionalProperties": False,
        }}},
        input=[
            {
                "role": "system",
                "content": KNOWLEDGE_AGENT_PROMPT,
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nContext:\n{context}",
            },
        ],
    )

    try:
        return json.loads(response.output_text)
    except (json.JSONDecodeError, AttributeError):
        return {
            "answer": response.output_text.strip() if hasattr(response, "output_text") else "I could not generate an answer.",
            "answer_confidence": 0.0,
            "is_password_related": False,
            "reasoning": "Failed to parse structured response.",
        }


def search(query: str, top_k: int = 3) -> dict:
    retrieved_docs = retrieve(query, top_k=top_k)
    result = generate_grounded_answer(query, retrieved_docs)
    return {
        "answer": result["answer"],
        "answer_confidence": result.get("answer_confidence", 0.0),
        "is_password_related": result.get("is_password_related", False),
        "reasoning": result.get("reasoning", ""),
        "sources": [doc["title"] for doc in retrieved_docs],
        "documents": retrieved_docs,
    }
