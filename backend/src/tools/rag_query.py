"""RAG query over post-mortems, runbooks and known issues.
Uses Qdrant (long_term memory) as primary source, falls back to local KB fixtures.
"""

from langchain_core.tools import tool


@tool
def rag_query(query: str, k: int = 4) -> str:
    """Search the knowledge base of post-mortems, runbooks and known issues
    for passages relevant to the query. Use this to find precedents for the
    current incident or to follow resolution procedures.
    """
    try:
        from src.memory.long_term import search_documents

        results = search_documents(query, k=k)
        if results:
            lines = [f"[{r['id']}] {r['text'][:200]}" for r in results]
            return "\n".join(lines)
    except Exception:
        pass

    # Fallback a KB local
    try:
        from src.db.fixtures import KB_DATA

        matching = [kb for kb in KB_DATA if query.lower() in kb.get("incident_type", "").lower()
                     or query.lower() in kb.get("symptom", "").lower()]
        if not matching:
            matching = KB_DATA[:2]
        lines = []
        for kb in matching:
            steps = " | ".join(kb.get("resolution_steps", []))
            lines.append(f"[{kb['incident_type']}] {kb['symptom']} → {kb['root_cause']} :: {steps}")
        return "\n".join(lines)
    except Exception:
        return "No knowledge base entries found."
