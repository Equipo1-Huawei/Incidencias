"""Containment worker — proposes remediation + guardrail. 1 LLM call + tools directas."""
from __future__ import annotations

from src.agent.base import build_hybrid_worker, load_prompt
from src.agent.guardrail import validate_commands, sanitize_commands
from src.tools.terraform_gen import generate_terraform


async def preprocess(state: dict) -> str:
    incident = state.get("incident", {})
    component = incident.get("component", "frontend")
    is_sec = incident.get("is_security_event", False)

    if is_sec:
        commands = "iptables -A INPUT -s 192.168.10.45 -j DROP\ndocker restart triage-nextjs"
    elif component == "database":
        commands = "docker restart triage-nextjs\ndocker logs triage-nextjs --tail 100"
    else:
        commands = "docker logs triage-nextjs --tail 100\ndocker stats --no-stream"

    validation = validate_commands(commands)
    if not validation["approved"]:
        commands = sanitize_commands(commands)

    tf = generate_terraform.invoke({"incident_type": "SQL Injection" if is_sec else "Infrastructure", "component": component})

    return f"Guardrail: {validation['approved']}\nReason: {validation['reason']}\nCommands:\n{commands}\n\nTerraform:\n{tf}"


def build():
    return build_hybrid_worker(
        name="containment",
        prompt=load_prompt("containment"),
        preprocess=preprocess,
        model_role="code",
    )
