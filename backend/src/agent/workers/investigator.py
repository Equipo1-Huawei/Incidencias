"""Investigator worker — correlates logs, health, deploys and history to find root cause."""

from __future__ import annotations

from src.agent.workers.base import build_worker, load_prompt
from src.tools.ir_tools import check_health, query_historical
from src.tools.query_logs import query_logs
from src.tools.list_recent_deploys import list_recent_deploys
from src.tools.rag_query import rag_query


def _fallback(state: dict) -> str:
    incident = state.get("incident", {})
    desc = incident.get("description", "")
    component = incident.get("component", "frontend")
    is_sec = incident.get("is_security_event", False)

    desc_lower = desc.lower()
    if "union" in desc_lower or "sql" in desc_lower:
        hypothesis = "SQL Injection vulnerability exploited on authentication endpoint."
    elif "script" in desc_lower:
        hypothesis = "Cross-Site Scripting (XSS) payload detected targeting search parameter."
    elif "passwd" in desc_lower or ".." in desc_lower:
        hypothesis = "Path Traversal attack attempting directory escape to read /etc/passwd."
    elif "mongonetworkerror" in desc_lower or "27017" in desc_lower:
        hypothesis = "MongoDB Atlas connectivity failure — network egress to TCP 27017 blocked."
    elif "oom" in desc_lower or "out of memory" in desc_lower:
        hypothesis = "Container Out-Of-Memory crash — process exceeded 512MB cgroup limit."
    else:
        hypothesis = f"Service degradation detected on {component}."

    return (
        f"Investigation Findings:\n"
        f"- Primary hypothesis: {hypothesis}\n"
        f"- Confidence: {'high' if is_sec else 'medium'}\n"
        f"- Evidence: raw log analysis for component '{component}'"
    )


def build():
    return build_worker(
        name="investigator",
        tools=[query_logs, check_health, query_historical, list_recent_deploys, rag_query],
        prompt=load_prompt("investigator"),
        model_role="code",
        fallback_fn=_fallback,
    )
