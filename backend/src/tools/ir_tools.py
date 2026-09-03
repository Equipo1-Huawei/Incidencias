"""LangChain @tool wrappers around Pato's existing IR tools (validators, queries, analyzers).
These let the workers call them via the ReAct agent pattern.
"""

from langchain_core.tools import tool


@tool
def validate_incident(description: str) -> str:
    """Analyze a log line or incident description for cybersecurity signatures
    (SQLi, XSS, Path Traversal) and extract the affected component.
    Use this as the first step when triaging a new incident.
    """
    import json
    from src.tools.validators import validate_incident_description
    res = validate_incident_description(description)
    return json.dumps(res, default=str)


@tool
def check_health(component: str) -> str:
    """Check the live operational health of a component via HTTP healthcheck.
    Returns status, latency and whether the service is operational.
    Use this to verify if a service is actually down.
    """
    import json
    import asyncio
    from src.tools.queries import check_component_health

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = pool.submit(asyncio.run, check_component_health(component)).result()
        else:
            res = loop.run_until_complete(check_component_health(component))
    except Exception:
        res = asyncio.run(check_component_health(component))
    return json.dumps(res, default=str)


@tool
def query_historical(component: str, incident_type: str = "") -> str:
    """Query MongoDB Atlas for past incidents matching the component and type.
    Returns historical incidents with MTTD/MTTR averages. Use this to find
    precedents and estimate resolution time.
    """
    import json
    import asyncio
    from src.tools.queries import query_historical_incidents

    try:
        res = asyncio.run(query_historical_incidents(component, incident_type or None))
    except Exception:
        res = {"error": "Could not query historical incidents"}
    return json.dumps(res, default=str)


@tool
def search_known_issues(incident_type: str, component: str) -> str:
    """Search the knowledge base for known solutions matching the incident type
    and component. Returns resolution steps and confidence scores.
    Use this to find established remediation procedures.
    """
    import json
    import asyncio
    from src.tools.queries import search_solutions_in_kb

    try:
        res = asyncio.run(search_solutions_in_kb(incident_type, component))
    except Exception:
        res = []
    return json.dumps(res, default=str)


@tool
def calculate_risk(component: str, severity: str, is_operational: bool,
                   is_security_event: bool = False) -> str:
    """Calculate the risk score (0-10), severity level, escalation team and
    SLA targets for an incident. Use this after gathering evidence to determine
    urgency and routing.
    """
    import json
    from src.tools.analyzers import calculate_risk_score, estimate_sla

    risk = calculate_risk_score(
        component=component,
        severity=severity,
        is_operational=is_operational,
        is_security_event=is_security_event,
    )
    sla = estimate_sla(risk.get("severity", severity))
    return json.dumps({"risk": risk, "sla": sla}, default=str)
