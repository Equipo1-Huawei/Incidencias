"""Containment worker — proposes and validates defensive remediation."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.langchain_tools import validate_guardrail, sanitize_guardrail
from src.tools.terraform_gen import generate_terraform


def build():
    return build_worker(
        name="containment",
        tools=[validate_guardrail, sanitize_guardrail, generate_terraform],
        prompt=load_prompt("containment"),
        model_role="code",
    )
