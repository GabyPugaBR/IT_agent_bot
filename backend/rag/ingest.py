import json
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import get_embeddings

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base.txt"
INDEX_PATH = BASE_DIR / "knowledge.index"
METADATA_PATH = BASE_DIR / "knowledge_metadata.json"


def load_source_text() -> str:
    return KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8").strip()


def chunk_knowledge_base() -> list[dict]:
    sections = [section.strip() for section in load_source_text().split("\n\n") if section.strip()]
    chunks = []

    for idx, section in enumerate(sections):
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        title = lines[0]
        content = " ".join(lines[1:]) if len(lines) > 1 else lines[0]
        text = f"{title}\n{content}"
        chunks.append(
            {
                "id": idx,
                "title": title,
                "content": content,
                "text": text,
            }
        )

    return chunks


def build_index() -> dict:
    chunks = chunk_knowledge_base()
    embeddings = np.array(get_embeddings([chunk["text"] for chunk in chunks]), dtype="float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    return {
        "index": index,
        "chunks": chunks,
    }
