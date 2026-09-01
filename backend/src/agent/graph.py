from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import (
    node_analyze_incident,
    node_execute_tools,
    node_calculate_score,
    node_generate_output,
)

def create_triage_graph():
    """Construye y compila el grafo agéntico asíncrono."""
    graph = StateGraph(AgentState)

    graph.add_node("analyze", node_analyze_incident)
    graph.add_node("tools", node_execute_tools)
    graph.add_node("scoring", node_calculate_score)
    graph.add_node("output", node_generate_output)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "tools")
    graph.add_edge("tools", "scoring")
    graph.add_edge("scoring", "output")
    graph.add_edge("output", END)

    return graph.compile()

_compiled_graph = None

def get_triage_graph():
    """Retorna la instancia singleton compilada del grafo."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_triage_graph()
    return _compiled_graph
