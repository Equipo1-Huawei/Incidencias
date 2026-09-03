"""LangChain @tool wrappers for existing tools used by workers."""
from __future__ import annotations

import json
from langchain_core.tools import tool

from src.tools.validators import validate_incident_description
from src.tools.analyzers import calculate_risk_score, estimate_sla
from src.tools.queries import (
    check_component_health,
    query_historical_incidents,
    search_solutions_in_kb,
    save_incident_result,
    save_audit_event,
)
from src.agent.guardrail import validate_commands, sanitize_commands


@tool
def validate_incident(description: str) -> str:
    """Analyze a log line for cybersecurity attack signatures (SQLi, XSS, Path Traversal)
    and extract the affected component. Returns JSON with is_security_event, security_types,
    and extracted fields. Example: validate_incident("admin' UNION SELECT 1,2,3--")"""
    import asyncio
    result = validate_incident_description(description)
    return json.dumps(result, default=str)


@tool
def calculate_risk(component: str, severity: str, is_operational: bool, is_security_event: bool = False) -> str:
    """Calculate risk score (0-10) and assign escalation team.
    component: frontend/database/network/auth
    severity: P1/P2/P3
    is_operational: True if component is responding
    is_security_event: True if this is a cyber attack
    Returns JSON with risk_score, category, escalation_team."""
    result = calculate_risk_score(
        component=component,
        severity=severity,
        is_operational=is_operational,
        is_security_event=is_security_event,
    )
    return json.dumps(result, default=str)


@tool
def check_health(component: str) -> str:
    """Check the live health status of a component via HTTP.
    component: frontend/database/network/auth
    Returns JSON with status, latency_ms, is_operational."""
    import asyncio
    result = asyncio.run(check_component_health(component))
    return json.dumps(result, default=str)


@tool
def query_historical(component: str, incident_type: str = "") -> str:
    """Query Supabase for past incidents with the same component.
    Returns JSON with historical incidents, average MTTR and MTTD."""
    import asyncio
    result = asyncio.run(query_historical_incidents(component, incident_type or None))
    return json.dumps(result, default=str)


@tool
def search_kb(incident_type: str, component: str) -> str:
    """Search the knowledge base in Supabase for known remediation procedures.
    Returns matching solutions with resolution steps and confidence."""
    import asyncio
    result = asyncio.run(search_solutions_in_kb(incident_type, component))
    return json.dumps(result, default=str)


@tool
def save_incident(incident_data: str) -> str:
    """Persist the incident triage result to Supabase for audit and future reference.
    incident_data: JSON string with incident details."""
    import asyncio
    state = json.loads(incident_data) if isinstance(incident_data, str) else incident_data
    asyncio.run(save_incident_result(state))
    return "Incident saved to Supabase successfully."


@tool
def save_audit(event_type: str, incident_id: str = "", approved: bool = True, reason: str = "") -> str:
    """Save an audit event to Supabase. event_type: GUARDRAIL_CHECK, ACTION_EXECUTED, etc."""
    import asyncio
    asyncio.run(save_audit_event(
        event_type=event_type,
        incident_id=incident_id or None,
        approved=approved if approved else None,
        reason=reason or None,
    ))
    return "Audit event saved successfully."


@tool
def validate_guardrail(commands: str) -> str:
    """Validate that CLI commands are safe and non-destructive.
    Checks against 22 patterns: rm -rf, mkfs, DROP TABLE, fork bomb, nmap, sqlmap, etc.
    Returns JSON with approved (bool), reason, and blocked_patterns."""
    result = validate_commands(commands)
    return json.dumps(result, default=str)


@tool
def sanitize_guardrail(commands: str) -> str:
    """If commands contain destructive patterns, replace them with safe alternatives.
    Returns the sanitized command string."""
    return sanitize_commands(commands)
