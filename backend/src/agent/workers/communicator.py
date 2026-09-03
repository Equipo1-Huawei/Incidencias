"""Communicator worker — drafts status updates. 1 LLM call."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt


def build():
    return build_worker(
        name="communicator",
        tools=[],
        prompt=load_prompt("communicator"),
        model_role="code",
    )
