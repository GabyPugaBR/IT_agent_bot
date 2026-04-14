import json
import os
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import get_embeddings
from tools.mcp_client import fetch_confluence_pages_via_mcp

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "knowledge.index"
METADATA_PATH = BASE_DIR / "knowledge_metadata.json"


def current_source_signature() -> dict:
    page_ids = [page_id.strip() for page_id in os.getenv("CONFLUENCE_PAGE_ID", "").split(",") if page_id.strip()]
    return {
        "base_url": os.getenv("CONFLUENCE_BASE_URL"),
        "page_ids": page_ids,
    }


def load_source_documents() -> list[dict]:
    mcp_result = fetch_confluence_pages_via_mcp()
    if mcp_result.get("status") == "success" and mcp_result.get("pages"):
        return mcp_result["pages"]
    message = mcp_result.get("message", "Confluence knowledge fetch failed.")
    errors = mcp_result.get("errors", [])
    detail = f" Details: {'; '.join(errors)}" if errors else ""
    raise RuntimeError(f"{message}{detail}")


def _chunk_page(content: str, title: str, page_id: str, space: str, url: str,
                max_chars: int = 800, overlap: int = 100) -> list[dict]:
    """
    Split a page's content into overlapping paragraph-based chunks.
    Falls back to a single chunk for short pages.
    """
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [content.strip()]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap from end of previous
            current = current[-overlap:].strip() + "\n\n" + para if current else para

    if current:
        chunks.append(current)

    return [
        {
            "title": title,
            "content": chunk,
            "text": f"{title}\n{chunk}",
            "page_id": page_id,
            "space": space,
            "url": url,
        }
        for chunk in chunks
    ]


def chunk_knowledge_base() -> list[dict]:
    documents = load_source_documents()
    all_chunks = []
    chunk_id = 0

    for document in documents:
        title = document["title"]
        content = document["content"].strip()
        page_chunks = _chunk_page(
            content=content,
            title=title,
            page_id=document.get("id", ""),
            space=document.get("space", ""),
            url=document.get("url", ""),
        )
        for chunk in page_chunks:
            all_chunks.append({"id": chunk_id, **chunk})
            chunk_id += 1

    return all_chunks


def build_index() -> dict:
    mcp_result = fetch_confluence_pages_via_mcp()
    if mcp_result.get("status") != "success" or not mcp_result.get("pages"):
        message = mcp_result.get("message", "Confluence knowledge fetch failed.")
        errors = mcp_result.get("errors", [])
        detail = f" Details: {'; '.join(errors)}" if errors else ""
        raise RuntimeError(f"{message}{detail}")

    source_name = mcp_result.get("source", "confluence_cloud")
    documents = mcp_result["pages"]

    chunks = []
    chunk_id = 0
    for document in documents:
        title = document["title"]
        content = document["content"].strip()
        page_chunks = _chunk_page(
            content=content,
            title=title,
            page_id=document.get("id", ""),
            space=document.get("space", ""),
            url=document.get("url", ""),
        )
        for chunk in page_chunks:
            chunks.append({"id": chunk_id, **chunk})
            chunk_id += 1

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
