"""Communicator worker — drafts status updates. Reasoning-only (no tools)."""

from __future__ import annotations

from src.agent.workers.base import build_worker, load_prompt


def _fallback(state: dict) -> str:
    incident = state.get("incident", {})
    component = incident.get("component", "unknown")
    severity = incident.get("severity", "P2")
    is_sec = incident.get("is_security_event", False)
    scratchpad = state.get("scratchpad", {})

    root_cause = "Under investigation"
    if "investigator" in scratchpad:
        root_cause = scratchpad["investigator"][:200]

    incident_type = "Cybersecurity event" if is_sec else "Infrastructure failure"

    return (
        f"Status Update:\n"
        f"- Status: investigating\n"
        f"- Summary: {incident_type} detected on {component}.\n"
        f"- Severity: {severity}\n"
        f"- Affected service: {component}\n"
        f"- Root cause (preliminary): {root_cause}\n"
        f"- Actions taken: Triage and investigation in progress.\n"
        f"- Next steps: Remediation proposal pending.\n"
        f"- ETA: To be determined."
    )


def build():
    return build_worker(
        name="communicator",
        tools=[],
        prompt=load_prompt("communicator"),
        model_role="code",
        fallback_fn=_fallback,
    )
