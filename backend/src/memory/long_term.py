"""Long-term memory = Qdrant vector store with local embeddings (fastembed).
Indexes post-mortems and runbooks so the investigator and postmortem_writer
can cite precedents. Degrades gracefully if Qdrant is unavailable.
"""

from __future__ import annotations

from src.config import config

_COLLECTION = "knowledge"
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    from qdrant_client import QdrantClient

    _client = QdrantClient(url=config.QDRANT_URL)
    return _client


def index_documents(docs: list[dict]) -> int:
    """Index documents. Each doc: {"id": str, "text": str}. Returns count indexed."""
    client = _get_client()
    documents = [d["text"] for d in docs]
    ids = [d["id"] for d in docs]
    client.add(collection_name=_COLLECTION, documents=documents, ids=ids)
    return len(docs)


def search_documents(query: str, k: int = 4) -> list[dict]:
    """Return up to k passages most relevant to the query. Empty list if unavailable."""
    client = _get_client()
    try:
        results = client.query(collection_name=_COLLECTION, query_text=query, limit=k)
    except Exception:
        return []
    out = []
    for r in results:
        out.append({"id": str(getattr(r, "id", "")), "text": getattr(r, "document", "") or ""})
    return out
