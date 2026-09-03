"""Triage worker — classifies incidents. 1 LLM call + tools directas."""
from __future__ import annotations

import json
from src.agent.base import build_hybrid_worker, load_prompt
from src.tools.validators import validate_incident_description
from src.tools.analyzers import calculate_risk_score


async def preprocess(state: dict) -> str:
    incident = state.get("incident", {})
    raw_log = ""
    for msg in state.get("messages", []):
        if hasattr(msg, "content") and "Raw Log:" in msg.content:
            raw_log = msg.content.split("Raw Log:")[-1].strip()
            break
    if not raw_log:
        raw_log = incident.get("description", "")

    val = validate_incident_description(raw_log)
    is_sec = incident.get("is_security_event", False) or val.get("is_security_event", False)

    risk = calculate_risk_score(
        component=incident.get("component", val.get("extracted_fields", {}).get("component", "frontend")),
        severity=incident.get("severity", "P2"),
        is_operational=True,
        is_security_event=is_sec,
    )

    return json.dumps({"validation": val, "risk": risk}, default=str)


def build():
    return build_hybrid_worker(
        name="triage",
        prompt=load_prompt("triage"),
        preprocess=preprocess,
        model_role="code",
    )
