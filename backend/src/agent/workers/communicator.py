"""Communicator worker — drafts status updates for stakeholders."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.terraform_gen import generate_terraform


def build():
    return build_worker(
        name="communicator",
        tools=[generate_terraform],
        prompt=load_prompt("communicator"),
        model_role="code",
    )
