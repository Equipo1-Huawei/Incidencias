"""Triage worker — classifies incident severity, affected service, and security vs infra."""

from __future__ import annotations

from src.agent.workers.base import build_worker, load_prompt
from src.tools.ir_tools import validate_incident, search_known_issues


def _fallback(state: dict) -> str:
    incident = state.get("incident", {})
    desc = incident.get("description", "")
    component = incident.get("component", "frontend")
    is_sec = incident.get("is_security_event", False)
    severity = incident.get("severity", "P2")

    if is_sec or "union" in desc.lower() or "script" in desc.lower() or "passwd" in desc.lower():
        severity = "P1"
        classification = "CYBER_SECURITY_EVENT"
    else:
        classification = "INFRASTRUCTURE_FAILURE"

    return (
        f"Triage Result:\n"
        f"- Severity: {severity}\n"
        f"- Affected service: {component}\n"
        f"- Classification: {classification}\n"
        f"- Decision: ESCALATE"
    )


def build():
    return build_worker(
        name="triage",
        tools=[validate_incident, search_known_issues],
        prompt=load_prompt("triage"),
        model_role="code",
        fallback_fn=_fallback,
    )
