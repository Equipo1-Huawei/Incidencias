"""Mapeo e invocación de herramientas del agente."""
from src.tools.validators import validate_incident_description
from src.tools.queries import check_component_health, query_historical_incidents, search_solutions_in_kb
from src.tools.analyzers import calculate_risk_score, estimate_sla

TOOLS_MAP = {
    "validate_incident": validate_incident_description,
    "check_health": check_component_health,
    "query_historical": query_historical_incidents,
    "search_kb": search_solutions_in_kb,
    "calculate_risk": calculate_risk_score,
    "estimate_sla": estimate_sla,
}
