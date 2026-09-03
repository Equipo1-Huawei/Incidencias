"""Mapeo e invocacion de herramientas del agente."""
from src.tools.validators import validate_incident_description
from src.tools.queries import check_component_health, query_historical_incidents, search_solutions_in_kb, save_incident_result, save_audit_event
from src.tools.analyzers import calculate_risk_score, estimate_sla
from src.agent.guardrail import validate_commands, sanitize_commands

TOOLS_MAP = {
    "validate_incident": validate_incident_description,
    "check_health": check_component_health,
    "query_historical": query_historical_incidents,
    "search_kb": search_solutions_in_kb,
    "calculate_risk": calculate_risk_score,
    "estimate_sla": estimate_sla,
    "validate_commands": validate_commands,
    "sanitize_commands": sanitize_commands,
}
