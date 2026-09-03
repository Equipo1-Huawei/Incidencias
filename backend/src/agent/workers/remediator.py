"""Remediator worker — proposes corrective actions, gated behind human approval."""

from __future__ import annotations

from src.agent.workers.base import build_worker, load_prompt
from src.tools.ir_tools import calculate_risk
from src.tools.trigger_rollback import trigger_rollback, restart_service


def _fallback(state: dict) -> str:
    incident = state.get("incident", {})
    desc = incident.get("description", "")
    component = incident.get("component", "frontend")
    is_sec = incident.get("is_security_event", False)

    if is_sec:
        actions = [
            "GATED: Block offending source IP in Security Group/WAF (requires approval)",
            "GATED: Enable WAF strict filtering rules (requires approval)",
            "SAFE: Notify SOC team",
        ]
        team = "SOC"
        risk = 10.0
    elif "oom" in desc.lower() or "out of memory" in desc.lower():
        actions = [
            "GATED: Restart container triage-nextjs (requires approval)",
            "SAFE: Review memory limit in Docker Compose",
        ]
        team = "SRE_ONCALL"
        risk = 8.0
    elif "mongo" in desc.lower() or "27017" in desc.lower():
        actions = [
            "GATED: Restore egress network rule for TCP 27017 (requires approval)",
            "SAFE: Verify MongoDB Atlas cluster status",
        ]
        team = "SRE_ONCALL"
        risk = 8.5
    else:
        actions = [
            f"GATED: Rollback {component} to previous deployment (requires approval)",
            "SAFE: Monitor error rate after action",
        ]
        team = "PLATFORM_TEAM"
        risk = 6.0

    return (
        f"Remediation Plan:\n"
        f"- Risk score: {risk}/10.0\n"
        f"- Escalation team: {team}\n"
        f"- Actions:\n" + "\n".join(f"  - {a}" for a in actions)
    )


def build():
    return build_worker(
        name="remediator",
        tools=[calculate_risk, trigger_rollback, restart_service],
        prompt=load_prompt("remediator"),
        model_role="code",
        fallback_fn=_fallback,
    )
