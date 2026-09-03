"""Assembles the supervisor + workers into a compiled LangGraph.

    supervisor --Command(goto=worker)--> worker --edge--> supervisor --...--> END

Workers come from src/agent/workers/__init__.py::WORKERS (dict name -> node).
The supervisor gets a matching handoff tool automatically per worker.

An approval gate node is added between the remediator and any action execution.
When the remediator proposes a gated action, it writes `pending_approval` to the
state. The approval_gate node checks for this and interrupts the graph until a
human approves via POST /approve.
"""

from __future__ import annotations

from pathlib import Path

from langgraph.graph import START, StateGraph, END

from src.agent.state import AgentState
from src.agent.supervisor import build_supervisor
from src.tracing.logger import get_logger

log = get_logger("graph")

_PROMPTS = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def approval_gate(state: dict) -> dict:
    """Check if the remediator proposed a gated action. If so, mark it as pending.
    In a full implementation this would use langgraph.types.interrupt() to pause
    the graph. For the demo, we just flag it in the state so the UI can show
    an approval button.
    """
    scratchpad = state.get("scratchpad", {})
    remediator_output = scratchpad.get("remediator", "")

    if "GATED" in remediator_output or "requires approval" in remediator_output.lower():
        return {
            "pending_approval": {
                "action": remediator_output[:500],
                "status": "pending",
            },
            "status": "mitigating",
        }
    return {}


def build_graph(checkpointer=None):
    """Build and compile the multi-agent incident response graph."""
    from src.agent.workers import WORKERS

    worker_names = list(WORKERS.keys())
    supervisor = build_supervisor(worker_names, _load_prompt("supervisor"))

    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor)
    for name, node in WORKERS.items():
        g.add_node(name, node)
        g.add_edge(name, "supervisor")

    g.add_node("approval_gate", approval_gate)
    g.add_edge("remediator", "approval_gate")
    g.add_edge("approval_gate", "supervisor")

    g.add_edge(START, "supervisor")
    compiled = g.compile(checkpointer=checkpointer)
    return compiled


_compiled_graph = None


def get_triage_graph():
    """Retorna la instancia singleton compilada del grafo."""
    global _compiled_graph
    if _compiled_graph is None:
        from src.memory.short_term import get_checkpointer
        _compiled_graph = build_graph(checkpointer=get_checkpointer(persist=False))
    return _compiled_graph


def get_triage_graph_persistent():
    """Retorna el grafo con checkpointer persistente (SQLite)."""
    global _compiled_graph
    from src.memory.short_term import get_checkpointer
    _compiled_graph = build_graph(checkpointer=get_checkpointer(persist=True))
    return _compiled_graph
