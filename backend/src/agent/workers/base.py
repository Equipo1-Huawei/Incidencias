"""Factory for worker nodes — ported from arquitectura_multiagente/harness/agents/base.py.

A worker with tools is a ReAct agent (create_react_agent). A reasoning-only worker
(tools=[]) is a single LLM call. Either way the node takes the shared state, does its
work, and appends ONE message tagged with the worker's name, then the graph routes
back to the supervisor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from src.config import config
from src.tracing.logger import get_logger

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
log = get_logger("worker")


def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _get_worker_llm(model_role: str = "code"):
    """Build a ChatOpenAI for a worker. Falls back to None (deterministic mode)."""
    if config.PANGU_API_KEY:
        return ChatOpenAI(
            model=config.HUAWEI_MODEL,
            base_url=config.PANGU_BASE_URL.rstrip("/") + "/v1",
            api_key=config.PANGU_API_KEY,
            temperature=0.2,
            timeout=30,
            max_retries=2,
        )
    if config.OPENAI_FALLBACK_KEY:
        return ChatOpenAI(
            model=config.OPENAI_MODEL,
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_FALLBACK_KEY,
            temperature=0.2,
            timeout=30,
            max_retries=2,
        )
    return None


def build_worker(
    name: str,
    tools: list,
    prompt: str,
    model_role: str = "code",
    fallback_fn: Callable = None,
) -> Callable:
    llm = _get_worker_llm(model_role)

    if llm is not None and tools:
        agent = create_react_agent(llm, tools=tools)

        def worker_node(state: dict) -> dict:
            log.info("worker.start", worker=name, tools=[t.name for t in tools])
            msgs = [SystemMessage(content=prompt)] + _to_lc_messages(state.get("messages", []))
            if not msgs:
                msgs = [SystemMessage(content=prompt), HumanMessage(content="(no input)")]
            result = agent.invoke({"messages": msgs})
            last = result["messages"][-1]
            last.name = name
            return {"messages": [last], "scratchpad": {**state.get("scratchpad", {}), name: last.content}}

    elif llm is not None:
        def worker_node(state: dict) -> dict:
            log.info("worker.start", worker=name, tools=[])
            msgs = [SystemMessage(content=prompt)] + _to_lc_messages(state.get("messages", []))
            if not msgs:
                msgs = [SystemMessage(content=prompt), HumanMessage(content="(no input)")]
            ai = llm.invoke(msgs)
            ai.name = name
            return {"messages": [ai], "scratchpad": {**state.get("scratchpad", {}), name: ai.content}}

    else:
        def worker_node(state: dict) -> dict:
            log.info("worker.fallback", worker=name)
            content = fallback_fn(state) if fallback_fn else f"[{name}] No LLM available — fallback response."
            msg = AIMessage(content=content, name=name)
            return {"messages": [msg], "scratchpad": {**state.get("scratchpad", {}), name: content}}

    worker_node.__name__ = f"{name}_node"
    return worker_node


def _to_lc_messages(raw_messages: list):
    """Convert dict messages to LangChain messages if needed."""
    result = []
    for m in raw_messages:
        if hasattr(m, "content"):
            result.append(m)
        elif isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "assistant":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
    return result
