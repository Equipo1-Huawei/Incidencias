"""Postmortem writer — generates the post-mortem report once the incident is resolved."""

from __future__ import annotations

from src.agent.workers.base import build_worker, load_prompt
from src.tools.rag_query import rag_query


def _fallback(state: dict) -> str:
    incident = state.get("incident", {})
    incident_id = state.get("incident_id", "unknown")
    component = incident.get("component", "unknown")
    severity = incident.get("severity", "P2")
    is_sec = incident.get("is_security_event", False)
    scratchpad = state.get("scratchpad", {})

    root_cause = scratchpad.get("investigator", "Unknown")[:300]
    remediation = scratchpad.get("remediator", "No actions taken")[:300]

    return (
        f"# Post-Mortem Report — Incident {incident_id[:8]}\n\n"
        f"## 1. Executive Summary\n"
        f"- **Severity:** {severity}\n"
        f"- **Affected service:** {component}\n"
        f"- **Type:** {'Cybersecurity event' if is_sec else 'Infrastructure failure'}\n\n"
        f"## 2. Timeline\n"
        f"- Alert received → Triage → Investigation → Remediation → Resolved\n\n"
        f"## 3. Root Cause\n"
        f"> {root_cause}\n\n"
        f"## 4. Resolution\n"
        f"> {remediation}\n\n"
        f"## 5. Action Items\n"
        f"- [ ] Review monitoring thresholds for {component}\n"
        f"- [ ] Add automated alert for this failure mode\n\n"
        f"## 6. Lessons Learned\n"
        f"- Incident detected and triaged autonomously by the multi-agent system.\n"
        f"- Human-in-the-loop gate ensured no destructive action was taken without approval."
    )


def build():
    return build_worker(
        name="postmortem_writer",
        tools=[rag_query],
        prompt=load_prompt("postmortem_writer"),
        model_role="code",
        fallback_fn=_fallback,
    )
