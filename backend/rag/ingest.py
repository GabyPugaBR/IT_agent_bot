import json
import os
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import get_embeddings
from tools.mcp_client import fetch_confluence_pages_via_mcp

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base.txt"
INDEX_PATH = BASE_DIR / "knowledge.index"
METADATA_PATH = BASE_DIR / "knowledge_metadata.json"


def current_source_signature() -> dict:
    page_ids = [page_id.strip() for page_id in os.getenv("CONFLUENCE_PAGE_IDS", "").split(",") if page_id.strip()]
    return {
        "base_url": os.getenv("CONFLUENCE_BASE_URL"),
        "page_ids": page_ids,
    }


def load_source_documents() -> list[dict]:
    mcp_result = fetch_confluence_pages_via_mcp()
    if mcp_result.get("status") == "success" and mcp_result.get("pages"):
        return mcp_result["pages"]

    source_text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8").strip()
    sections = [section.strip() for section in source_text.split("\n\n") if section.strip()]
    documents = []
    for idx, section in enumerate(sections):
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        title = lines[0]
        content = " ".join(lines[1:]) if len(lines) > 1 else lines[0]
        documents.append(
            {
                "id": f"LOCAL-{idx}",
                "title": title,
                "space": "Local Knowledge Base",
                "url": None,
                "content": content,
            }
        )
    return documents


def chunk_knowledge_base() -> list[dict]:
    documents = load_source_documents()
    chunks = []

    for idx, document in enumerate(documents):
        title = document["title"]
        content = document["content"].strip()
        text = f"{title}\n{content}"
        chunks.append(
            {
                "id": idx,
                "title": title,
                "content": content,
                "text": text,
                "page_id": document.get("id"),
                "space": document.get("space"),
                "url": document.get("url"),
            }
        )

    return chunks


def build_index() -> dict:
    mcp_result = fetch_confluence_pages_via_mcp()
    if mcp_result.get("status") == "success" and mcp_result.get("pages"):
        source_name = mcp_result.get("source", "mcp_confluence")
        documents = mcp_result["pages"]
    else:
        source_name = "local_fallback"
        documents = load_source_documents()

    chunks = []
    for idx, document in enumerate(documents):
        title = document["title"]
        content = document["content"].strip()
        text = f"{title}\n{content}"
        chunks.append(
            {
                "id": idx,
                "title": title,
                "content": content,
                "text": text,
                "page_id": document.get("id"),
                "space": document.get("space"),
                "url": document.get("url"),
            }
        )

    embeddings = np.array(get_embeddings([chunk["text"] for chunk in chunks]), dtype="float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(
        json.dumps(
            {
                "source": source_name,
                "source_signature": current_source_signature(),
                "chunks": chunks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "index": index,
        "chunks": chunks,
    }
