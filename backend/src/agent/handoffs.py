"""Handoff tools — one `transfer_to_<worker>` tool per worker.
Calling a tool == delegating to that worker. Ported from arquitectura_multiagente.
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool


def make_handoff_tool(agent_name: str) -> StructuredTool:
    def _handoff(reason: str) -> str:
        return f"Delegated to {agent_name}: {reason}"

    return StructuredTool.from_function(
        func=_handoff,
        name=f"transfer_to_{agent_name}",
        description=(
            f"Delegate the current step to the '{agent_name}' worker. "
            f"Provide a short reason describing what you need it to do."
        ),
    )


FINISH = "FINISH"
