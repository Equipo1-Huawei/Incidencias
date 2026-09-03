"""Reporter worker — generates post-mortem + persists. 1 LLM call + tools directas."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from src.agent.base import build_hybrid_worker, load_prompt
from src.tools.queries import save_incident_result, save_audit_event


async def preprocess(state: dict) -> str:
    try:
        incident = state.get("incident", {})
        messages = state.get("messages", [])

        triage_state = {
            "incident": {
                "incident_id": incident.get("incident_id", "unknown"),
                "description": incident.get("description", ""),
                "component": incident.get("component", "frontend"),
                "severity": incident.get("severity", "P2"),
                "source": incident.get("source", "unknown"),
                "is_security_event": incident.get("is_security_event", False),
                "timestamp": incident.get("timestamp", datetime.now(timezone.utc)),
            },
            "identified_component": incident.get("component", "frontend"),
            "risk_score": state.get("risk_score", 0.0),
            "root_cause_hypothesis": state.get("root_cause_hypothesis", ""),
            "escalation_path": state.get("escalation_path", ""),
            "final_recommendation": state.get("final_recommendation", ""),
            "diagnostics_checklist": state.get("diagnostics_checklist", []),
            "diagnostic_steps": state.get("diagnostic_steps", []),
        }

        await save_incident_result(triage_state)

        incident_id = incident.get("incident_id", "unknown")
        await save_audit_event(
            event_type="INCIDENT_RESOLVED",
            incident_id=incident_id,
            actor="reporter_worker",
            approved=True,
            reason="Post-mortem generated and incident persisted to Supabase",
        )
        return f"Incident {incident_id} persisted to Supabase. Audit event saved."
    except Exception as e:
        return f"Persist failed (non-fatal): {e}"


def build():
    return build_hybrid_worker(
        name="reporter",
        prompt=load_prompt("reporter"),
        preprocess=preprocess,
        model_role="code",
    )
