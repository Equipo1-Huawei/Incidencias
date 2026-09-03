from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import (
    node_analyze_incident,
    node_execute_tools,
    node_calculate_score,
    node_generate_output,
    node_guardrail_validate,
    node_persist,
)
from src.logging_config import get_logger

logger = get_logger(__name__)


def _route_after_analyze(state: AgentState) -> str:
    """Si es un evento de seguridad critico, saltar healthcheck e ir directo a scoring."""
    incident = state.get("incident", {})
    is_sec = incident.get("is_security_event", False)
    if is_sec:
        logger.info("graph.shortcut", reason="security_event", route="analyze->scoring")
        return "scoring"
    return "tools"


def create_triage_graph():
    """Construye y compila el grafo agentico asincrono con guardrail y branching."""
    graph = StateGraph(AgentState)

    graph.add_node("analyze", node_analyze_incident)
    graph.add_node("tools", node_execute_tools)
    graph.add_node("scoring", node_calculate_score)
    graph.add_node("output", node_generate_output)
    graph.add_node("guardrail", node_guardrail_validate)
    graph.add_node("persist", node_persist)

    graph.set_entry_point("analyze")

    graph.add_conditional_edges(
        "analyze",
        _route_after_analyze,
        {"tools": "tools", "scoring": "scoring"}
    )

    graph.add_edge("tools", "scoring")
    graph.add_edge("scoring", "output")
    graph.add_edge("output", "guardrail")
    graph.add_edge("guardrail", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


_compiled_graph = None

def get_triage_graph():
    """Retorna la instancia singleton compilada del grafo."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_triage_graph()
        logger.info("graph.compiled")
    return _compiled_graph
