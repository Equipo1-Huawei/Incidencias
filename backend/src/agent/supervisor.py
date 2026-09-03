"""Central supervisor node."""
from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END
from langgraph.types import Command

from src.llm import get_llm
from src.agent.handoffs import make_handoff_tool
from src.agent.policies import should_stop
from src.tracing import get_logger
from src.tracing.cost import cost_snapshot

log = get_logger("supervisor")


def build_supervisor(worker_names: list[str], system_prompt: str) -> Callable:
    tools = [make_handoff_tool(n) for n in worker_names]
    llm_router = get_llm("think", temperature=0.0).bind_tools(tools)

    def supervisor(state: dict) -> Command:
        stop, reason = should_stop(state)
        if stop:
            log.info("supervisor.stop", reason=reason)
            msg = AIMessage(content=f"[stopped: {reason}]", name="supervisor")
            return Command(goto=END, update={"next_agent": "FINISH", "messages": [msg]})

        sys = system_prompt.replace("{workers}", ", ".join(worker_names))
        response = llm_router.invoke([SystemMessage(content=sys)] + state["messages"])

        loops = state.get("loop_count", 0)
        usd = cost_snapshot()["usd"]

        if getattr(response, "tool_calls", None):
            target = response.tool_calls[0]["name"].replace("transfer_to_", "")
            if target not in worker_names:
                log.info("supervisor.unknown_worker", target=target)
                return Command(
                    goto=END,
                    update={"next_agent": "FINISH", "messages": [response]},
                )
            log.info("supervisor.route", to=target, loop=loops + 1)
            return Command(
                goto=target,
                update={
                    "next_agent": target,
                    "loop_count": loops + 1,
                    "total_cost_usd": usd,
                },
            )

        log.info("supervisor.finish", loop=loops)
        return Command(
            goto=END,
            update={"next_agent": "FINISH", "total_cost_usd": usd, "messages": [response]},
        )

    return supervisor
