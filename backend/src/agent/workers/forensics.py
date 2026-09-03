"""Forensics worker — investigates root cause. 1 LLM call + tools directas."""
from __future__ import annotations

import json
from src.agent.base import build_hybrid_worker, load_prompt
from src.tools.queries import check_component_health, query_historical_incidents, search_solutions_in_kb


async def preprocess(state: dict) -> str:
    incident = state.get("incident", {})
    component = incident.get("component", "frontend")
    incident_type = state.get("identified_type", "Anomaly")

    health = await check_component_health(component)
    historical = await query_historical_incidents(component, incident_type)
    kb = await search_solutions_in_kb(incident_type, component)

    return json.dumps({
        "health": health,
        "historical": {"count": historical.get("total_incidents", 0), "avg_mttr": historical.get("average_mttr_minutes"), "incidents": historical.get("incidents", [])[:2]},
        "kb_solutions": kb[:2] if isinstance(kb, list) else kb,
    }, default=str)


def build():
    return build_hybrid_worker(
        name="forensics",
        prompt=load_prompt("forensics"),
        preprocess=preprocess,
        model_role="code",
    )
