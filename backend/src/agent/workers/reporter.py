"""Reporter worker — generates post-mortem + persists. 1 LLM call + tools directas."""
from __future__ import annotations

from src.agent.base import build_hybrid_worker, load_prompt
from src.tools.queries import save_incident_result, save_audit_event


async def preprocess(state: dict) -> str:
    try:
        await save_incident_result(state)
        incident_id = state.get("incident", {}).get("incident_id", "unknown")
        await save_audit_event(
            event_type="INCIDENT_RESOLVED",
            incident_id=incident_id,
            actor="reporter_worker",
            approved=True,
            reason="Post-mortem generated and incident persisted",
        )
        return "Incident persisted to Supabase. Audit event saved."
    except Exception as e:
        return f"Persist failed (non-fatal): {e}"


def build():
    return build_hybrid_worker(
        name="reporter",
        prompt=load_prompt("reporter"),
        preprocess=preprocess,
        model_role="code",
    )
