"""Triage worker — classifies and prioritizes incidents."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.langchain_tools import validate_incident, calculate_risk


def build():
    return build_worker(
        name="triage",
        tools=[validate_incident, calculate_risk],
        prompt=load_prompt("triage"),
        model_role="code",
    )
