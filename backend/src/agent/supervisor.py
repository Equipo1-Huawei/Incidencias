"""Central supervisor node — delegates to workers via handoff tools.
Ported from arquitectura_multiagente/harness/orchestrator/supervisor.py, adapted
to use Pato's ResilientLLMClient for inference and ChatOpenAI for tool-calling.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command

from src.agent.handoffs import make_handoff_tool
from src.agent.policies import should_stop
from src.config import config
from src.tracing.logger import get_logger

log = get_logger("supervisor")


def _get_router_llm():
    """Build a ChatOpenAI for the supervisor. Uses Pangu/Kostra if available,
    falls back to OpenAI, or a no-op model if neither is configured."""
    if config.PANGU_API_KEY:
        return ChatOpenAI(
            model=config.HUAWEI_MODEL,
            base_url=config.PANGU_BASE_URL.rstrip("/") + "/v1",
            api_key=config.PANGU_API_KEY,
            temperature=0.0,
            timeout=30,
            max_retries=2,
        )
    if config.OPENAI_FALLBACK_KEY:
        return ChatOpenAI(
            model=config.OPENAI_MODEL,
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_FALLBACK_KEY,
            temperature=0.0,
            timeout=30,
            max_retries=2,
        )
    # No real key — return None, supervisor will use fallback routing
    return None


def build_supervisor(worker_names: list[str], system_prompt: str) -> Callable:
    tools = [make_handoff_tool(n) for n in worker_names]
    llm_router = _get_router_llm()
    if llm_router is not None:
        llm_router = llm_router.bind_tools(tools)

    def supervisor(state: dict) -> Command:
        stop, reason = should_stop(state)
        if stop:
            log.info("supervisor.stop", reason=reason)
            msg = AIMessage(content=f"[stopped: {reason}]", name="supervisor")
            return Command(goto=END, update={"next_agent": "FINISH", "messages": [msg]})

        sys = system_prompt.replace("{workers}", ", ".join(worker_names))

        if llm_router is None:
            return _fallback_route(state, worker_names, sys)

        messages = [SystemMessage(content=sys)] + _to_lc_messages(state.get("messages", []))
        response = llm_router.invoke(messages)

        loops = state.get("loop_count", 0)

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
                },
            )

        log.info("supervisor.finish", loop=loops)
        return Command(
            goto=END,
            update={"next_agent": "FINISH", "messages": [response]},
        )

    return supervisor


def _to_lc_messages(raw_messages: list):
    """Convert dict messages to LangChain messages if needed."""
    from langchain_core.messages import HumanMessage, AIMessage as LCAIMessage

    result = []
    for m in raw_messages:
        if hasattr(m, "content"):
            result.append(m)
        elif isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "assistant":
                result.append(LCAIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
    return result


def _fallback_route(state: dict, worker_names: list[str], sys: str) -> Command:
    """Deterministic fallback routing when no LLM is available.
    Follows the standard incident flow: triage → investigator → communicator → remediator → postmortem_writer.
    Uses loop_count to track position in the flow (more reliable than next_agent).
    """
    loops = state.get("loop_count", 0)

    flow = ["triage", "investigator", "communicator", "remediator", "postmortem_writer"]
    flow = [w for w in flow if w in worker_names]

    # loops increments each time the supervisor routes. 0 = first call.
    # After the flow completes once, finish.
    if loops >= len(flow):
        log.info("supervisor.finish.fallback", loop=loops)
        msg = AIMessage(content="[fallback] Incident response flow complete. Post-mortem generated.", name="supervisor")
        return Command(goto=END, update={"next_agent": "FINISH", "messages": [msg], "status": "resolved"})

    target = flow[loops]
    log.info("supervisor.route.fallback", to=target, loop=loops + 1)
    return Command(
        goto=target,
        update={"next_agent": target, "loop_count": loops + 1},
    )
