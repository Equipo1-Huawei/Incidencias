"""RAG query tool — searches indexed documents in Qdrant."""
from __future__ import annotations

from langchain_core.tools import tool

from src.memory.long_term import search_documents


@tool
def rag_query(query: str, k: int = 4) -> str:
    """Search the internal knowledge base (runbooks, post-mortems, known issues) for
    passages relevant to the query. Returns top matching passages with document ids."""
    try:
        hits = search_documents(query, k=k)
    except Exception as e:
        return f"rag_query unavailable ({e}). Is Qdrant running and seeded?"

    if not hits:
        return "No indexed documents matched. Knowledge base may be empty."

    return "\n\n".join(f"[{h['id']}] {h['text']}" for h in hits)
