"""Reporter worker — generates post-mortem and persists results."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.langchain_tools import save_incident, save_audit


def build():
    return build_worker(
        name="reporter",
        tools=[save_incident, save_audit],
        prompt=load_prompt("reporter"),
        model_role="code",
    )
