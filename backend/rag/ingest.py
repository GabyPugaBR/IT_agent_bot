import json
import os
import re
from hashlib import sha256
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


def source_content_signature(documents: list[dict]) -> str:
    payload = [
        {
            "id": document.get("id", ""),
            "title": document.get("title", ""),
            "version": document.get("version"),
            "updated_at": document.get("updated_at"),
            "content": document.get("content", ""),
        }
        for document in documents
    ]
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def load_source_payload() -> dict:
    mcp_result = fetch_confluence_pages_via_mcp()
    if mcp_result.get("status") == "success" and mcp_result.get("pages"):
        return mcp_result
    message = mcp_result.get("message", "Confluence knowledge fetch failed.")
    errors = mcp_result.get("errors", [])
    detail = f" Details: {'; '.join(errors)}" if errors else ""
    raise RuntimeError(f"{message}{detail}")


def load_source_documents() -> list[dict]:
    return load_source_payload()["pages"]


def _is_section_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 90:
        return False
    if line[-1:] in {".", "?", "!", ",", ";"}:
        return False

    words = re.findall(r"[A-Za-z0-9-]+", line)
    if not 2 <= len(words) <= 10:
        return False

    title_like_words = sum(1 for word in words if word[:1].isupper() or word.isupper())
    return title_like_words / len(words) >= 0.6


def _split_sections(content: str, fallback_title: str) -> list[dict]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return [{"heading": fallback_title, "body": ""}]

    sections = []
    current_heading = fallback_title
    current_lines = []

    for line in lines:
        if _is_section_heading(line):
            if current_lines:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_lines).strip(),
                })
            current_heading = line
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_lines).strip(),
        })

    if not sections:
        return [{"heading": fallback_title, "body": "\n".join(lines).strip()}]

    return sections


def _split_long_section(text: str, max_chars: int, overlap: int) -> list[str]:
    units = [unit.strip() for unit in re.split(r"(?<=[.!?])\s+|\n+", text) if unit.strip()]
    if not units:
        return [text.strip()] if text.strip() else []

    chunks = []
    current_units = []
    current_length = 0

    for unit in units:
        projected_length = current_length + len(unit) + (1 if current_units else 0)
        if current_units and projected_length > max_chars:
            chunks.append(" ".join(current_units).strip())
            overlap_text = chunks[-1][-overlap:].strip()
            current_units = [overlap_text, unit] if overlap_text else [unit]
            current_length = sum(len(item) for item in current_units) + len(current_units) - 1
        else:
            current_units.append(unit)
            current_length = projected_length

    if current_units:
        chunks.append(" ".join(current_units).strip())

    return chunks


def _chunk_page(content: str, title: str, page_id: str, space: str, url: str,
                version=None, updated_at: str | None = None,
                max_chars: int = 700, overlap: int = 80) -> list[dict]:
    """
    Split a page into heading-aware chunks so retrieval stays focused.
    """
    chunks = []
    sections = _split_sections(content, fallback_title=title)

    for section in sections:
        heading = section["heading"]
        body = section["body"]
        section_text = f"{heading}\n{body}".strip()
        section_chunks = (
            [section_text]
            if len(section_text) <= max_chars
            else _split_long_section(section_text, max_chars=max_chars, overlap=overlap)
        )

        for index, chunk in enumerate(section_chunks):
            chunks.append(
                {
                    "title": title,
                    "section_title": heading,
                    "content": chunk,
                    "text": f"{title}\nSection: {heading}\n{chunk}",
                    "page_id": page_id,
                    "space": space,
                    "url": url,
                    "version": version,
                    "updated_at": updated_at,
                    "chunk_index": index,
                }
            )

    return chunks


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
            version=document.get("version"),
            updated_at=document.get("updated_at"),
        )
        for chunk in page_chunks:
            all_chunks.append({"id": chunk_id, **chunk})
            chunk_id += 1

    return all_chunks


def build_index(mcp_result: dict | None = None) -> dict:
    mcp_result = mcp_result or fetch_confluence_pages_via_mcp()
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
            version=document.get("version"),
            updated_at=document.get("updated_at"),
        )
        for chunk in page_chunks:
            chunks.append({"id": chunk_id, **chunk})
            chunk_id += 1

    if not chunks:
        raise RuntimeError("Confluence knowledge fetch returned no indexable content.")

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
                "source_content_signature": source_content_signature(documents),
                "document_count": len(documents),
                "chunk_count": len(chunks),
                "chunks": chunks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "index": index,
        "chunks": chunks,
        "source_content_signature": source_content_signature(documents),
    }
