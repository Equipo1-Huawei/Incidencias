"""Short-term memory = LangGraph checkpointer. Persists each thread so an incident
can be resumed (useful for HITL: the graph pauses at approval and resumes later).

Uses an in-memory saver by default; pass persist=True for a SQLite-backed one.
"""

from __future__ import annotations


def get_checkpointer(persist: bool = False):
    if persist:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver

            return SqliteSaver.from_conn_string("data/ckpt.db")
        except Exception:
            pass
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()
