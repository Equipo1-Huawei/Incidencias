"""Shared state that flows through the whole graph.

Extends LangGraph's MessagesState with incident response fields.
"""
from __future__ import annotations

from typing import Any, Optional

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    plan: list[str]
    scratchpad: dict[str, Any]
    citations: list[dict]
    next_agent: Optional[str]
    loop_count: int
    total_cost_usd: float
    incident_id: str
    severity: Optional[str]
    affected_services: list[str]
    iocs: list[dict]
    timeline: list[dict]
    actions_taken: list[dict]
    pending_approval: Optional[dict]
    status: str
    risk_score: float
    guardrail_approved: bool
    guardrail_reason: Optional[str]


def initial_state(user_message, incident_id: str = "") -> dict:
    return {
        "messages": [user_message],
        "plan": [],
        "scratchpad": {},
        "citations": [],
        "next_agent": None,
        "loop_count": 0,
        "total_cost_usd": 0.0,
        "incident_id": incident_id,
        "severity": None,
        "affected_services": [],
        "iocs": [],
        "timeline": [],
        "actions_taken": [],
        "pending_approval": None,
        "status": "investigating",
        "risk_score": 0.0,
        "guardrail_approved": True,
        "guardrail_reason": None,
    }
