"""Short-term memory = LangGraph checkpointer."""
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
