"""Assembles the supervisor + workers into a compiled LangGraph."""
from __future__ import annotations

from pathlib import Path

from langgraph.graph import START, StateGraph

from src.agent.state import AgentState
from src.agent.supervisor import build_supervisor
from src.tracing import get_logger

log = get_logger("graph")

_PROMPTS = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def build_graph(checkpointer=None):
    from src.agent.workers import WORKERS

    worker_names = list(WORKERS.keys())
    supervisor = build_supervisor(worker_names, _load_prompt("supervisor"))

    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor)
    for name, node in WORKERS.items():
        g.add_node(name, node)
        g.add_edge(name, "supervisor")

    g.add_edge(START, "supervisor")
    log.info("graph.compiled", workers=worker_names)
    return g.compile(checkpointer=checkpointer)


_compiled_graph = None


def get_triage_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
