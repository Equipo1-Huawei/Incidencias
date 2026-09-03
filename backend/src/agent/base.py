"""Factory for worker nodes."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from src.llm import get_llm
from src.tracing import get_logger

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
log = get_logger("worker")


def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def build_worker(
    name: str,
    tools: list,
    prompt: str,
    model_role: str = "code",
) -> Callable:
    llm = get_llm(model_role)

    if tools:
        agent = create_react_agent(llm, tools=tools)

        def worker_node(state: dict) -> dict:
            log.info("worker.start", worker=name, tools=[t.name for t in tools])
            msgs = [SystemMessage(content=prompt)] + state["messages"]
            result = agent.invoke({"messages": msgs})
            last = result["messages"][-1]
            last.name = name
            return {"messages": [last]}
    else:

        def worker_node(state: dict) -> dict:
            log.info("worker.start", worker=name, tools=[])
            msgs = [SystemMessage(content=prompt)] + state["messages"]
            ai = llm.invoke(msgs)
            ai.name = name
            return {"messages": [ai]}

    worker_node.__name__ = f"{name}_node"
    return worker_node
