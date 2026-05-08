import json
import os
import time
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import KNOWLEDGE_AGENT_PROMPT
from rag.embeddings import get_embedding
from rag.ingest import (
    INDEX_PATH,
    METADATA_PATH,
    build_index,
    current_source_signature,
    load_source_payload,
    source_content_signature,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
REFRESH_INTERVAL_SECONDS = int(os.getenv("RAG_REFRESH_INTERVAL_SECONDS", "60"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_STORE = None


def _cache_is_fresh() -> bool:
    if _STORE is None:
        return False
    loaded_at = _STORE.get("loaded_at", 0)
    return time.time() - loaded_at < REFRESH_INTERVAL_SECONDS


def _store_from_index(index, metadata_payload: dict) -> dict:
    return {
        "index": index,
        "chunks": metadata_payload.get("chunks", []),
        "source_content_signature": metadata_payload.get("source_content_signature"),
        "loaded_at": time.time(),
    }


def load_store(force_refresh: bool = False) -> dict:
    global _STORE
    if not force_refresh and _STORE is not None and _cache_is_fresh():
        return _STORE

    if force_refresh or not INDEX_PATH.exists() or not METADATA_PATH.exists():
        _STORE = build_index()
        _STORE["loaded_at"] = time.time()
        return _STORE

    try:
        index = faiss.read_index(str(INDEX_PATH))
        metadata_payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, json.JSONDecodeError):
        _STORE = build_index()
        _STORE["loaded_at"] = time.time()
        return _STORE

    if isinstance(metadata_payload, list):
        _STORE = build_index()
        _STORE["loaded_at"] = time.time()
        return _STORE

    if metadata_payload.get("source_signature") != current_source_signature():
        _STORE = build_index()
        _STORE["loaded_at"] = time.time()
        return _STORE

    try:
        source_payload = load_source_payload()
        live_signature = source_content_signature(source_payload["pages"])
    except RuntimeError:
        _STORE = _store_from_index(index, metadata_payload)
        return _STORE

    if metadata_payload.get("source_content_signature") != live_signature:
        _STORE = build_index(source_payload)
        _STORE["loaded_at"] = time.time()
        return _STORE

    _STORE = _store_from_index(index, metadata_payload)
    return _STORE


def rebuild_store() -> dict:
    return load_store(force_refresh=True)


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
        (
            f"Source: {doc['title']}\n"
            f"Section: {doc.get('section_title', doc['title'])}\n"
            f"Content: {doc['content']}"
        )
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
        "sources": [
            f"{doc['title']} - {doc.get('section_title', doc['title'])}"
            for doc in retrieved_docs
        ],
        "documents": retrieved_docs,
    }
